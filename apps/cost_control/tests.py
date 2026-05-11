from decimal import Decimal
from datetime import date
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from .models import ActualCost, BudgetItem, CostCode
from .services import (
    calculate_cpi, calculate_cost_variance, calculate_eac, get_cost_summary,
)

User = get_user_model()


def _make_project(user, contract_no='TEST-001'):
    return Project.objects.create(
        project_name=f'Project {contract_no}',
        contract_no=contract_no,
        owner='Owner',
        contractor='Contractor',
        start_date=date(2025, 1, 1),
        finish_date=date(2025, 12, 31),
        contract_value=Decimal('1000000.00'),
        status='Active',
        created_by=user,
    )


class CpiCalculationTests(TestCase):
    def test_normal_cpi(self):
        cpi = calculate_cpi(Decimal('600000'), Decimal('500000'))
        self.assertEqual(cpi, Decimal('1.20'))

    def test_overrun_cpi(self):
        cpi = calculate_cpi(Decimal('400000'), Decimal('500000'))
        self.assertEqual(cpi, Decimal('0.80'))

    def test_zero_actual_returns_none(self):
        self.assertIsNone(calculate_cpi(Decimal('100000'), Decimal('0')))

    def test_zero_ev_zero_ac(self):
        self.assertIsNone(calculate_cpi(Decimal('0'), Decimal('0')))


class CostVarianceTests(TestCase):
    def test_positive_variance(self):
        cv = calculate_cost_variance(Decimal('600000'), Decimal('500000'))
        self.assertEqual(cv, Decimal('100000'))

    def test_negative_variance(self):
        cv = calculate_cost_variance(Decimal('400000'), Decimal('500000'))
        self.assertEqual(cv, Decimal('-100000'))

    def test_zero_variance(self):
        cv = calculate_cost_variance(Decimal('500000'), Decimal('500000'))
        self.assertEqual(cv, Decimal('0'))


class EacCalculationTests(TestCase):
    def test_normal_eac(self):
        eac = calculate_eac(Decimal('1000000'), Decimal('1.20'))
        self.assertAlmostEqual(float(eac), 833333.33, places=1)

    def test_eac_cpi_below_one(self):
        eac = calculate_eac(Decimal('1000000'), Decimal('0.80'))
        self.assertAlmostEqual(float(eac), 1250000.00, places=1)

    def test_none_cpi_returns_none(self):
        self.assertIsNone(calculate_eac(Decimal('1000000'), None))

    def test_zero_cpi_returns_none(self):
        self.assertIsNone(calculate_eac(Decimal('1000000'), Decimal('0')))


class CostSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('tester', password='pw', role='admin')
        self.project = _make_project(self.user)
        self.code = CostCode.objects.create(
            project=self.project, code='A01', name='Civil Works'
        )

    def test_empty_project_returns_zeros(self):
        summary = get_cost_summary(self.project)
        self.assertEqual(summary['total_budget'], 0.0)
        self.assertEqual(summary['actual_cost'], 0.0)
        self.assertEqual(summary['cost_status'], 'N/A')
        self.assertIsNone(summary['cpi'])
        self.assertIsNone(summary['eac'])

    def test_zero_actual_cost_is_na(self):
        BudgetItem.objects.create(
            project=self.project, cost_code=self.code,
            description='Foundation', budget_amount=Decimal('500000')
        )
        summary = get_cost_summary(self.project)
        self.assertEqual(summary['cost_status'], 'N/A')
        self.assertIsNone(summary['cpi'])

    def test_actual_cost_recorded(self):
        BudgetItem.objects.create(
            project=self.project, cost_code=self.code,
            description='Foundation', budget_amount=Decimal('1000000')
        )
        ActualCost.objects.create(
            project=self.project, cost_code=self.code,
            cost_date=date.today(), description='Labour',
            amount=Decimal('200000'), source_type='Labor',
            created_by=self.user,
        )
        summary = get_cost_summary(self.project)
        self.assertEqual(summary['actual_cost'], 200000.0)
        self.assertEqual(summary['total_budget'], 1000000.0)

    def test_summary_keys_present(self):
        summary = get_cost_summary(self.project)
        for key in ('total_budget', 'committed', 'actual_cost', 'earned_value',
                    'cost_variance', 'cpi', 'eac', 'cost_status', 'cost_status_class'):
            self.assertIn(key, summary)


class DashboardIntegrationTests(TestCase):
    """Ensure the main dashboard loads without error whether or not cost data exists."""

    def setUp(self):
        self.user = User.objects.create_user('dashuser', password='pw', role='admin')
        self.client = Client()
        self.client.force_login(self.user)

    def test_dashboard_loads_without_cost_data(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/index.html')

    def test_dashboard_loads_with_cost_data(self):
        project = _make_project(self.user, 'COST-001')
        code = CostCode.objects.create(project=project, code='A01', name='Civil')
        BudgetItem.objects.create(
            project=project, cost_code=code,
            description='Foundation', budget_amount=Decimal('500000')
        )
        ActualCost.objects.create(
            project=project, cost_code=code,
            cost_date=date.today(), description='Materials',
            amount=Decimal('200000'), source_type='Material',
            created_by=self.user,
        )
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_cost_dashboard_loads(self):
        response = self.client.get('/cost-control/')
        self.assertEqual(response.status_code, 200)
