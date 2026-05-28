from django.db.models import Q
from django.utils import timezone

from .models import InspectionRequest, NonConformance, PunchList


def get_overdue_ncr_queryset(projects=None, today=None):
    """Open or in-progress NCRs with due dates before today."""
    today = today or timezone.localdate()
    queryset = NonConformance.objects.exclude(
        status__in=[NonConformance.STATUS_CLOSED, NonConformance.STATUS_CANCELLED]
    ).filter(due_date__lt=today)
    if projects is not None:
        queryset = queryset.filter(project__in=list(projects))
    return queryset


def calculate_inspection_approval_rate(projects=None):
    """Approved inspections divided by submitted/approved/rejected/closed inspections."""
    queryset = InspectionRequest.objects.all()
    if projects is not None:
        queryset = queryset.filter(project__in=list(projects))

    accountable_statuses = [
        InspectionRequest.STATUS_SUBMITTED,
        InspectionRequest.STATUS_APPROVED,
        InspectionRequest.STATUS_REJECTED,
        InspectionRequest.STATUS_CLOSED,
    ]
    total = queryset.filter(status__in=accountable_statuses).count()
    if total == 0:
        return 0.0
    approved = queryset.filter(status=InspectionRequest.STATUS_APPROVED).count()
    return round(approved / total * 100, 1)


def get_quality_metrics(projects=None):
    """Return dashboard-ready quality metrics. Safe for empty datasets."""
    projects = list(projects) if projects is not None else None
    inspections = InspectionRequest.objects.all()
    ncrs = NonConformance.objects.all()
    punch_items = PunchList.objects.all()

    if projects is not None:
        inspections = inspections.filter(project__in=projects)
        ncrs = ncrs.filter(project__in=projects)
        punch_items = punch_items.filter(project__in=projects)

    return {
        'inspection_submitted': inspections.filter(status=InspectionRequest.STATUS_SUBMITTED).count(),
        'inspection_approved': inspections.filter(status=InspectionRequest.STATUS_APPROVED).count(),
        'inspection_rejected': inspections.filter(status=InspectionRequest.STATUS_REJECTED).count(),
        'pending_inspection': inspections.filter(
            status__in=[InspectionRequest.STATUS_DRAFT, InspectionRequest.STATUS_SUBMITTED],
            result=InspectionRequest.RESULT_PENDING,
        ).count(),
        'ncr_open': ncrs.filter(status__in=[NonConformance.STATUS_OPEN, NonConformance.STATUS_IN_PROGRESS]).count(),
        'ncr_closed': ncrs.filter(status=NonConformance.STATUS_CLOSED).count(),
        'punch_list_open': punch_items.filter(status__in=[PunchList.STATUS_OPEN, PunchList.STATUS_IN_PROGRESS]).count(),
        'punch_list_closed': punch_items.filter(status=PunchList.STATUS_CLOSED).count(),
        'quality_approval_rate': calculate_inspection_approval_rate(projects),
    }


def get_quality_dashboard_tables(projects=None, today=None, limit=5):
    """Return short querysets for owner reporting tables."""
    today = today or timezone.localdate()
    projects = list(projects) if projects is not None else None

    ncrs = NonConformance.objects.select_related('project', 'responsible_person')
    inspections = InspectionRequest.objects.select_related('project', 'requested_by', 'inspected_by')
    punch_items = PunchList.objects.select_related('project', 'responsible_person')

    if projects is not None:
        ncrs = ncrs.filter(project__in=projects)
        inspections = inspections.filter(project__in=projects)
        punch_items = punch_items.filter(project__in=projects)

    return {
        'latest_ncr': ncrs.order_by('-issued_date', '-id')[:limit],
        'overdue_ncr': get_overdue_ncr_queryset(projects, today).select_related('project', 'responsible_person').order_by('due_date')[:limit],
        'pending_inspections': inspections.filter(
            status__in=[InspectionRequest.STATUS_DRAFT, InspectionRequest.STATUS_SUBMITTED],
            result=InspectionRequest.RESULT_PENDING,
        ).order_by('inspection_date')[:limit],
        'critical_punch_list': punch_items.filter(
            ~Q(status=PunchList.STATUS_CLOSED),
            priority=PunchList.PRIORITY_CRITICAL,
        ).order_by('target_date')[:limit],
    }
