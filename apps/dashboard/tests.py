from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from datetime import date
from decimal import Decimal

from apps.boq.models import BOQItem, DailyProgressRecord
from apps.projects.models import Project


class DashboardQualityIntegrationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='dashboard-quality',
            password='pw',
            role='admin',
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_dashboard_loads_without_quality_data(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')
        self.assertIn('quality_metrics', response.context)
        self.assertEqual(response.context['quality_metrics']['ncr_open'], 0)


def make_project(user, contract_no, name, value='1000000.00', status='Active'):
    return Project.objects.create(
        project_name=name,
        contract_no=contract_no,
        owner='Owner',
        contractor='Contractor',
        start_date=date(2026, 1, 1),
        finish_date=date(2026, 12, 31),
        contract_value=Decimal(value),
        status=status,
        created_by=user,
    )


def add_boq_progress(project, quantity='100.000', completed='25.000'):
    item = BOQItem.objects.create(
        project=project,
        item_no='1',
        description='Test BOQ item',
        unit='m',
        contract_quantity=Decimal(quantity),
        unit_rate=Decimal('100.00'),
    )
    DailyProgressRecord.objects.create(
        project=project,
        boq_item=item,
        record_date=date(2026, 5, 1),
        daily_quantity=Decimal(completed),
    )
    return item


class ExecutiveDashboardProjectFilterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='dashboard-filter',
            password='pw',
            role='admin',
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_project_filter_limits_executive_dashboard_scope(self):
        project_a = make_project(self.user, 'P-A', 'Project A', value='1000000.00')
        project_b = make_project(self.user, 'P-B', 'Project B', value='2000000.00')
        add_boq_progress(project_a, completed='50.000')
        add_boq_progress(project_b, completed='25.000')

        response = self.client.get(f'/?project={project_b.pk}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_project'], project_b)
        self.assertEqual(response.context['active_projects'], [project_b])
        self.assertEqual(response.context['dashboard_scope_label'], 'Project B')
        self.assertEqual(response.context['active_projects_count'], 1)
        self.assertEqual(response.context['total_contract_value'], 2000000.0)
        self.assertEqual([row['project'] for row in response.context['project_overview']], [project_b])
        self.assertContains(response, f'value="{project_b.pk}" selected')

    def test_default_scope_uses_all_active_projects(self):
        active = make_project(self.user, 'P-ACT', 'Active Project')
        completed = make_project(self.user, 'P-CMP', 'Completed Project', status='Completed')
        add_boq_progress(active)
        add_boq_progress(completed)

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['selected_project'])
        self.assertEqual(response.context['active_projects'], [active])
        self.assertEqual(response.context['dashboard_scope_label'], 'All Active Projects')
        self.assertEqual([row['project'] for row in response.context['project_overview']], [active])
