from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.projects.models import Project

from .models import InspectionRequest, NonConformance, PunchList
from .services import (
    calculate_inspection_approval_rate,
    get_overdue_ncr_queryset,
    get_quality_metrics,
)

User = get_user_model()


def make_user(username='quality-user'):
    return User.objects.create_user(username=username, password='pw', role='admin')


def make_project(user, contract_no='Q-001'):
    return Project.objects.create(
        project_name=f'Quality Project {contract_no}',
        contract_no=contract_no,
        owner='Owner',
        contractor='Contractor',
        start_date=date(2026, 1, 1),
        finish_date=date(2026, 12, 31),
        contract_value=Decimal('1000000.00'),
        status='Active',
        created_by=user,
    )


class QualityServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)

    def test_overdue_ncr_logic_excludes_closed_and_future_items(self):
        today = date(2026, 5, 11)
        overdue = NonConformance.objects.create(
            project=self.project,
            ncr_no='NCR-001',
            description='Concrete honeycomb',
            issued_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
            status=NonConformance.STATUS_OPEN,
            severity=NonConformance.SEVERITY_HIGH,
        )
        NonConformance.objects.create(
            project=self.project,
            ncr_no='NCR-002',
            description='Closed old item',
            issued_date=today - timedelta(days=10),
            due_date=today - timedelta(days=1),
            status=NonConformance.STATUS_CLOSED,
            severity=NonConformance.SEVERITY_LOW,
        )
        NonConformance.objects.create(
            project=self.project,
            ncr_no='NCR-003',
            description='Future due item',
            issued_date=today,
            due_date=today + timedelta(days=7),
            status=NonConformance.STATUS_OPEN,
            severity=NonConformance.SEVERITY_MEDIUM,
        )

        self.assertEqual(list(get_overdue_ncr_queryset([self.project], today)), [overdue])

    def test_inspection_approval_rate_uses_accountable_statuses(self):
        statuses = [
            InspectionRequest.STATUS_SUBMITTED,
            InspectionRequest.STATUS_APPROVED,
            InspectionRequest.STATUS_APPROVED,
            InspectionRequest.STATUS_REJECTED,
            InspectionRequest.STATUS_DRAFT,
        ]
        for idx, status in enumerate(statuses, start=1):
            InspectionRequest.objects.create(
                project=self.project,
                inspection_date=date(2026, 5, idx),
                location='Pier A',
                inspection_type='Rebar',
                description='Inspection request',
                requested_by=self.user,
                status=status,
            )

        self.assertEqual(calculate_inspection_approval_rate([self.project]), 50.0)

    def test_quality_metrics_service_empty_data_is_safe(self):
        metrics = get_quality_metrics([self.project])

        self.assertEqual(metrics['inspection_submitted'], 0)
        self.assertEqual(metrics['inspection_approved'], 0)
        self.assertEqual(metrics['inspection_rejected'], 0)
        self.assertEqual(metrics['pending_inspection'], 0)
        self.assertEqual(metrics['ncr_open'], 0)
        self.assertEqual(metrics['ncr_closed'], 0)
        self.assertEqual(metrics['punch_list_open'], 0)
        self.assertEqual(metrics['punch_list_closed'], 0)
        self.assertEqual(metrics['quality_approval_rate'], 0.0)

    def test_quality_metrics_service_counts_dashboard_values(self):
        InspectionRequest.objects.create(
            project=self.project,
            inspection_date=date(2026, 5, 1),
            location='Pier A',
            inspection_type='Concrete',
            description='Pour inspection',
            requested_by=self.user,
            status=InspectionRequest.STATUS_SUBMITTED,
        )
        InspectionRequest.objects.create(
            project=self.project,
            inspection_date=date(2026, 5, 2),
            location='Pier B',
            inspection_type='Rebar',
            description='Rebar inspection',
            requested_by=self.user,
            status=InspectionRequest.STATUS_APPROVED,
            result=InspectionRequest.RESULT_PASS,
        )
        NonConformance.objects.create(
            project=self.project,
            ncr_no='NCR-010',
            description='Failed cube test',
            issued_date=date(2026, 5, 1),
            due_date=date(2026, 5, 15),
            status=NonConformance.STATUS_OPEN,
            severity=NonConformance.SEVERITY_CRITICAL,
        )
        PunchList.objects.create(
            project=self.project,
            description='Repair surface defect',
            location='Zone 1',
            target_date=date(2026, 5, 20),
            status=PunchList.STATUS_OPEN,
            priority=PunchList.PRIORITY_CRITICAL,
        )

        metrics = get_quality_metrics([self.project])

        self.assertEqual(metrics['inspection_submitted'], 1)
        self.assertEqual(metrics['inspection_approved'], 1)
        self.assertEqual(metrics['pending_inspection'], 1)
        self.assertEqual(metrics['ncr_open'], 1)
        self.assertEqual(metrics['punch_list_open'], 1)
        self.assertEqual(metrics['quality_approval_rate'], 50.0)
