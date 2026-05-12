from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.projects.models import Project

from .models import DailyManpowerRecord, ManpowerCategory
from .services import get_manpower_dashboard_metrics


User = get_user_model()


def make_user(username='manpower-user'):
    return User.objects.create_user(username=username, password='pw', role='admin')


def make_project(user, contract_no='MP-001'):
    return Project.objects.create(
        project_name=f'Manpower Project {contract_no}',
        contract_no=contract_no,
        owner='Owner',
        contractor='Contractor',
        start_date=date(2026, 1, 1),
        finish_date=date(2026, 12, 31),
        contract_value=Decimal('1000000.00'),
        status='Active',
        created_by=user,
    )


class ManpowerDashboardTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)
        self.engineer = ManpowerCategory.objects.create(name='Engineer')
        self.worker = ManpowerCategory.objects.create(name='GeneralWorker')
        self.client = Client()
        self.client.force_login(self.user)

    def test_metrics_group_manpower_by_role(self):
        DailyManpowerRecord.objects.create(
            project=self.project,
            report_date=date(2026, 5, 1),
            category=self.engineer,
            company='Demo Construction Co.',
            quantity=3,
        )
        DailyManpowerRecord.objects.create(
            project=self.project,
            report_date=date(2026, 5, 1),
            category=self.worker,
            company='Demo Construction Co.',
            quantity=20,
        )
        DailyManpowerRecord.objects.create(
            project=self.project,
            report_date=date(2026, 5, 2),
            category=self.worker,
            company='Demo Construction Co.',
            quantity=22,
        )

        metrics = get_manpower_dashboard_metrics(
            [self.project],
            start_date=date(2026, 5, 1),
            end_date=date(2026, 5, 2),
        )

        self.assertEqual(metrics['total_manpower'], 45)
        self.assertEqual(metrics['active_roles'], 2)
        self.assertEqual(metrics['peak_role']['role'], 'General Worker')
        self.assertEqual(metrics['peak_role']['total'], 42)

    def test_dashboard_loads_without_manpower_data(self):
        response = self.client.get('/manpower/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'manpower/dashboard.html')
        self.assertIn('metrics', response.context)
        self.assertEqual(response.context['metrics']['total_manpower'], 0)
