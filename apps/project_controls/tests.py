from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.projects.models import Project
from apps.project_controls.models import SandDailyRecord
from apps.project_controls.services import get_sand_dashboard_data, recalculate_sand_accumulatives


User = get_user_model()


def make_user():
    return User.objects.create_user(username='project-controls-user', password='pw', role='admin')


def make_project(user):
    return Project.objects.create(
        project_name='Project Controls Test',
        contract_no='PC-001',
        owner='Owner',
        contractor='Contractor',
        start_date=date(2026, 1, 1),
        finish_date=date(2026, 12, 31),
        contract_value=Decimal('1000000.00'),
        status='Active',
        created_by=user,
    )


class ProjectControlsDashboardTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def test_rock_dashboard_loads_without_rock_data(self):
        response = self.client.get('/project-controls/rock/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project_controls/rock/dashboard.html')
        self.assertIn('data', response.context)
        self.assertEqual(response.context['data']['chart_data'], '{}')

    def test_sand_dashboard_loads_without_sand_data(self):
        response = self.client.get('/project-controls/sand/dashboard/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'project_controls/sand/dashboard.html')
        self.assertIn('data', response.context)
        self.assertEqual(response.context['data']['chart_data'], '{}')

    def test_sand_destinations_and_sources_are_calculated_separately(self):
        SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('100.00'),
            mtp3_daily_ton=Decimal('200.00'),
            chalothon_daily_ton=Decimal('120.00'),
            khlong_bang_phai_daily_ton=Decimal('180.00'),
        )
        recalculate_sand_accumulatives(self.project)

        metrics = get_sand_dashboard_data(self.project)

        self.assertEqual(metrics['total_accum'], 300.0)
        self.assertEqual(metrics['total_source_accum'], 300.0)
        self.assertEqual(metrics['total_chalothon'], 120.0)
        self.assertEqual(metrics['total_khlong_bang_phai'], 180.0)
