"""
Management command: python manage.py generate_notifications

Scans the database for actionable conditions and creates in-app notifications.
Designed to be run daily via cron or Windows Task Scheduler.
Deduplicates: will not re-notify the same user for the same type within 23 hours.
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.urls import reverse

from apps.accounts.models import User
from apps.notifications.utils import notify_if_new


APPROVER_ROLES = ['admin', 'project_manager', 'construction_manager']
MAINTENANCE_ROLES = ['admin', 'project_manager', 'construction_manager',
                     'office_engineer', 'engineer', 'site_engineer']
DRAWINGS_ROLES = ['admin', 'project_manager', 'construction_manager',
                  'office_engineer', 'engineer']


def _approvers():
    return User.objects.filter(role__in=APPROVER_ROLES, is_active=True)


def _users_with_roles(roles):
    return User.objects.filter(role__in=roles, is_active=True)


class Command(BaseCommand):
    help = 'Generate in-app notifications for overdue/pending items'

    def handle(self, *args, **options):
        today   = date.today()
        created = 0

        # ── Maintenance: overdue work orders ─────────────────────────────────
        try:
            from apps.maintenance.models import MaintenanceWorkOrder
            overdue_wo = MaintenanceWorkOrder.objects.filter(
                status__in=('Open', 'InProgress'),
                planned_date__lt=today,
            ).count()
            if overdue_wo:
                url   = reverse('maintenance:wo_list') + '?status=Open'
                title = f'{overdue_wo} Work Order{"s" if overdue_wo > 1 else ""} Overdue'
                msg   = f'{overdue_wo} maintenance work order(s) have passed their planned date.'
                for user in _users_with_roles(MAINTENANCE_ROLES):
                    if notify_if_new(user, 'maintenance_overdue', title, msg, url):
                        created += 1
        except Exception:
            pass

        # ── Maintenance: PM schedules due within 7 days ───────────────────────
        try:
            from apps.maintenance.models import MaintenanceSchedule
            due_soon = MaintenanceSchedule.objects.filter(
                is_active=True,
                next_due_date__range=(today, today + timedelta(days=7)),
            ).count()
            if due_soon:
                url   = reverse('maintenance:schedule_list')
                title = f'{due_soon} PM Schedule{"s" if due_soon > 1 else ""} Due This Week'
                msg   = f'{due_soon} preventive maintenance schedule(s) are due within 7 days.'
                for user in _users_with_roles(MAINTENANCE_ROLES):
                    if notify_if_new(user, 'maintenance_due_soon', title, msg, url):
                        created += 1
        except Exception:
            pass

        # ── Drawings: overdue RFIs ────────────────────────────────────────────
        try:
            from apps.drawings.models import RFI
            overdue_rfi = RFI.objects.filter(
                status__in=('Open', 'Submitted', 'UnderReview'),
                response_required_date__lt=today,
            ).count()
            if overdue_rfi:
                url   = reverse('drawings:rfi_list') + '?status=Submitted'
                title = f'{overdue_rfi} RFI{"s" if overdue_rfi > 1 else ""} Overdue'
                msg   = f'{overdue_rfi} RFI(s) have passed their required response date.'
                for user in _users_with_roles(DRAWINGS_ROLES):
                    if notify_if_new(user, 'rfi_overdue', title, msg, url):
                        created += 1
        except Exception:
            pass

        # ── HR: pending leave requests ────────────────────────────────────────
        try:
            from apps.hr.models import LeaveRequest
            pending_leave = LeaveRequest.objects.filter(status='Submitted').count()
            if pending_leave:
                url   = reverse('hr:leave_list') + '?status=Submitted'
                title = f'{pending_leave} Leave Request{"s" if pending_leave > 1 else ""} Pending'
                msg   = f'{pending_leave} leave request(s) are awaiting approval.'
                for user in _approvers():
                    if notify_if_new(user, 'leave_pending', title, msg, url):
                        created += 1
        except Exception:
            pass

        # ── HR: pending OT requests ───────────────────────────────────────────
        try:
            from apps.hr.models import OvertimeRequest
            pending_ot = OvertimeRequest.objects.filter(status='Draft').count()
            if pending_ot:
                url   = reverse('hr:ot_list') + '?status=Draft'
                title = f'{pending_ot} OT Request{"s" if pending_ot > 1 else ""} Pending'
                msg   = f'{pending_ot} overtime request(s) are awaiting approval.'
                for user in _approvers():
                    if notify_if_new(user, 'ot_pending', title, msg, url):
                        created += 1
        except Exception:
            pass

        # ── Subcontractors: payment claims pending ────────────────────────────
        try:
            from apps.subcontractors.models import PaymentClaim
            pending_claims = PaymentClaim.objects.filter(
                status__in=('Submitted', 'Certified')
            ).count()
            if pending_claims:
                url   = reverse('subcontractors:dashboard')
                title = f'{pending_claims} Payment Claim{"s" if pending_claims > 1 else ""} Pending'
                msg   = f'{pending_claims} payment claim(s) are awaiting certification or payment.'
                for user in _approvers():
                    if notify_if_new(user, 'claim_pending', title, msg, url):
                        created += 1
        except Exception:
            pass

        # ── Change Orders: pending review ─────────────────────────────────────
        try:
            from apps.change_orders.models import ChangeOrder
            pending_co = ChangeOrder.objects.filter(
                status__in=('Submitted', 'UnderReview')
            ).count()
            if pending_co:
                url   = reverse('change_orders:list') + '?status=Submitted'
                title = f'{pending_co} Change Order{"s" if pending_co > 1 else ""} Pending'
                msg   = f'{pending_co} change order(s) are awaiting review or approval.'
                for user in _approvers():
                    if notify_if_new(user, 'co_pending', title, msg, url):
                        created += 1
        except Exception:
            pass

        self.stdout.write(
            self.style.SUCCESS(f'generate_notifications: created {created} new notification(s).')
        )
