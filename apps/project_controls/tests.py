from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from apps.projects.models import Project
from apps.project_controls.forms import (
    RecoveryPlanDailyItemFormSet,
    RevetmentDailyRecordForm,
    RockDailyRecordForm,
    SandDailyRecordForm,
)
from apps.project_controls.models import (
    Barge,
    RockBargePlacement,
    RockDailyRecord,
    RockDashboardSettings,
    RockStationProgress,
    SandAreaProgress,
    SandBargePlacement,
    SandDailyRecord,
    SandDashboardSettings,
)
from apps.project_controls.services import (
    get_rock_dashboard_data,
    get_sand_dashboard_data,
    recalculate_rock_accumulatives,
    recalculate_sand_accumulatives,
)


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


class SandDailyRecordFormTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)

    def test_record_date_renders_native_date_value(self):
        record = SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 10),
            day_name='Sun',
        )

        form = SandDailyRecordForm(instance=record)

        self.assertIn('type="date"', str(form['record_date']))
        self.assertIn('value="2026-05-10"', str(form['record_date']))
        self.assertIn('readonly', str(form['day_name']))

    def test_all_project_control_day_name_fields_are_readonly(self):
        rock = RockDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 10),
            day_name='Sun',
        )
        sand = SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 11),
            day_name='Mon',
        )

        self.assertIn('readonly', str(RockDailyRecordForm(instance=rock)['day_name']))
        self.assertIn('readonly', str(SandDailyRecordForm(instance=sand)['day_name']))
        self.assertIn('readonly', str(RevetmentDailyRecordForm()['day_name']))
        self.assertIn('readonly', str(RecoveryPlanDailyItemFormSet().empty_form['day_name']))


class SandDailyRecordEditTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)
        self.client = Client()
        self.client.force_login(self.user)
        self.record = SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 10),
            day_name='Sun',
            tct_daily_ton=Decimal('252.00'),
            tct_trips=6,
            tct_trucks=1,
            mtp3_daily_ton=Decimal('916.20'),
            mtp3_trips=28,
            mtp3_trucks=9,
            khlong_bang_phai_daily_ton=Decimal('364.00'),
            offshore_daily_ton=Decimal('2982.78'),
            offshore_station='45145.914',
            onshore_daily_ton=Decimal('27128.54'),
            onshore_trucks=500,
            remaining_tct=Decimal('500.00'),
            remaining_mtp3=Decimal('5900.00'),
            created_by=self.user,
        )
        self.barge_a = Barge.objects.get(name='Bang Sapan 2')
        self.barge_b = Barge.objects.get(name='MTP8')
        self.placement_a = SandBargePlacement.objects.create(
            record=self.record,
            barge=self.barge_a,
            quantity_ton=Decimal('18.00'),
            trips=None,
            destination='Offshore Placement',
            placement_type=SandBargePlacement.PLACEMENT_OFFSHORE,
        )
        self.placement_b = SandBargePlacement.objects.create(
            record=self.record,
            barge=self.barge_b,
            quantity_ton=Decimal('1532.20'),
            trips=None,
            destination='Offshore Placement',
            placement_type=SandBargePlacement.PLACEMENT_OFFSHORE,
        )

    def test_edit_saves_existing_barge_placements(self):
        response = self.client.post(
            f'/project-controls/sand/{self.record.pk}/edit/',
            {
                'project': self.project.pk,
                'record_date': '2026-05-10',
                'day_name': 'Wrong',
                'tct_daily_ton': '252.00',
                'tct_trips': '6',
                'tct_trucks': '1',
                'mtp3_daily_ton': '916.20',
                'mtp3_trips': '28',
                'mtp3_trucks': '9',
                'chalothon_daily_ton': '0',
                'chalothon_trips': '0',
                'chalothon_trucks': '0',
                'khlong_bang_phai_daily_ton': '364.00',
                'khlong_bang_phai_trips': '0',
                'khlong_bang_phai_trucks': '0',
                'offshore_daily_ton': '2982.78',
                'offshore_station': '45145.914',
                'onshore_daily_ton': '27128.54',
                'onshore_trips': '0',
                'onshore_trucks': '500',
                'inside_plot_daily': '0',
                'outside_plot_daily': '0',
                'remaining_tct': '500.00',
                'remaining_mtp3': '5900.00',
                'remarks': '',
                'barge_placements-TOTAL_FORMS': '6',
                'barge_placements-INITIAL_FORMS': '2',
                'barge_placements-MIN_NUM_FORMS': '0',
                'barge_placements-MAX_NUM_FORMS': '1000',
                'barge_placements-0-id': self.placement_a.pk,
                'barge_placements-0-barge': self.barge_a.pk,
                'barge_placements-0-quantity_ton': '20.00',
                'barge_placements-0-trips': '',
                'barge_placements-0-source': '',
                'barge_placements-0-destination': 'Offshore Placement',
                'barge_placements-0-placement_type': 'Offshore',
                'barge_placements-0-station': '',
                'barge_placements-1-id': self.placement_b.pk,
                'barge_placements-1-barge': self.barge_b.pk,
                'barge_placements-1-quantity_ton': '1532.20',
                'barge_placements-1-trips': '',
                'barge_placements-1-source': '',
                'barge_placements-1-destination': 'Offshore Placement',
                'barge_placements-1-placement_type': 'Offshore',
                'barge_placements-1-station': '',
                'barge_placements-2-barge': '',
                'barge_placements-2-quantity_ton': '0',
                'barge_placements-2-trips': '',
                'barge_placements-2-source': '',
                'barge_placements-2-destination': '',
                'barge_placements-2-placement_type': 'Offshore',
                'barge_placements-2-station': '',
                'barge_placements-3-barge': '',
                'barge_placements-3-quantity_ton': '0',
                'barge_placements-3-trips': '',
                'barge_placements-3-source': '',
                'barge_placements-3-destination': '',
                'barge_placements-3-placement_type': 'Offshore',
                'barge_placements-3-station': '',
                'barge_placements-4-barge': '',
                'barge_placements-4-quantity_ton': '0',
                'barge_placements-4-trips': '',
                'barge_placements-4-source': '',
                'barge_placements-4-destination': '',
                'barge_placements-4-placement_type': 'Offshore',
                'barge_placements-4-station': '',
                'barge_placements-5-barge': '',
                'barge_placements-5-quantity_ton': '0',
                'barge_placements-5-trips': '',
                'barge_placements-5-source': '',
                'barge_placements-5-destination': '',
                'barge_placements-5-placement_type': 'Offshore',
                'barge_placements-5-station': '',
            },
        )

        self.assertRedirects(response, f'/project-controls/sand/{self.record.pk}/')
        self.record.refresh_from_db()
        self.placement_a.refresh_from_db()
        self.assertEqual(self.record.day_name, 'Sun')
        self.assertEqual(self.placement_a.quantity_ton, Decimal('20.00'))
        self.assertEqual(self.record.offshore_daily_ton, Decimal('1552.20'))


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

    def test_rock_available_stock_formula(self):
        RockDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
            placed_daily_ton=Decimal('700.00'),
        )
        recalculate_rock_accumulatives(self.project)

        metrics = get_rock_dashboard_data(self.project)

        self.assertEqual(metrics['total_delivered'], 1000.0)
        self.assertEqual(metrics['total_placed'], 700.0)
        self.assertEqual(metrics['available_stock_balance'], 300.0)

    def test_rock_target_metrics_when_settings_exist(self):
        RockDashboardSettings.objects.create(
            project=self.project,
            target_quantity_ton=Decimal('2000.00'),
            daily_target_placement_ton=Decimal('500.00'),
        )
        RockDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
            placed_daily_ton=Decimal('750.00'),
        )
        recalculate_rock_accumulatives(self.project)

        metrics = get_rock_dashboard_data(self.project)

        self.assertEqual(metrics['placement_completion_percent'], 37.5)
        self.assertEqual(metrics['remaining_quantity_to_boq'], 1250.0)

    def test_rock_barge_missing_trips_are_not_reported_as_zero(self):
        record = RockDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
        )
        barge = Barge.objects.create(name='Barge A', code='BA')
        RockBargePlacement.objects.create(
            record=record,
            barge=barge,
            quantity_ton=Decimal('400.00'),
            trips=None,
        )

        metrics = get_rock_dashboard_data(self.project)

        self.assertIsNone(metrics['barge_totals'][0]['total_trips'])
        self.assertIsNone(metrics['barge_totals'][0]['average_tons_per_trip'])

    def test_rock_station_status_logic(self):
        RockDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
            placed_daily_ton=Decimal('500.00'),
        )
        recalculate_rock_accumulatives(self.project)
        RockStationProgress.objects.create(
            project=self.project,
            station_range='0+000 - 0+100',
            material_type=RockDailyRecord.MATERIAL_CORE,
            delivered_quantity_ton=Decimal('1000.00'),
            placed_quantity_ton=Decimal('500.00'),
            target_quantity_ton=Decimal('1000.00'),
        )

        metrics = get_rock_dashboard_data(self.project)

        self.assertEqual(metrics['station_rows'][0]['completion_percent'], 50.0)
        self.assertEqual(metrics['station_rows'][0]['status'], 'In Progress')

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

    def test_sand_current_stock_balance_formula(self):
        SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('500.00'),
            mtp3_daily_ton=Decimal('500.00'),
            offshore_daily_ton=Decimal('250.00'),
            onshore_daily_ton=Decimal('150.00'),
        )
        recalculate_sand_accumulatives(self.project)

        metrics = get_sand_dashboard_data(self.project)

        self.assertEqual(metrics['total_delivered'], 1000.0)
        self.assertEqual(metrics['total_placed'], 400.0)
        self.assertEqual(metrics['current_stock_balance'], 600.0)

    def test_sand_target_metrics_when_settings_exist(self):
        SandDashboardSettings.objects.create(
            project=self.project,
            target_quantity_ton=Decimal('2000.00'),
            daily_target_delivery_ton=Decimal('400.00'),
            daily_target_placement_ton=Decimal('200.00'),
        )
        SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
            offshore_daily_ton=Decimal('600.00'),
        )
        recalculate_sand_accumulatives(self.project)

        metrics = get_sand_dashboard_data(self.project)

        self.assertEqual(metrics['completion_percent'], 30.0)
        self.assertEqual(metrics['remaining_quantity'], 1400.0)
        self.assertEqual(metrics['forecast_completion_date'], date(2026, 5, 4))

    def test_sand_barge_missing_trips_are_not_reported_as_zero(self):
        record = SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
        )
        barge = Barge.objects.create(name='Sand Barge A', code='SBA')
        SandBargePlacement.objects.create(
            record=record,
            barge=barge,
            quantity_ton=Decimal('400.00'),
            trips=None,
        )

        metrics = get_sand_dashboard_data(self.project)

        self.assertIsNone(metrics['barge_totals'][0]['total_trips'])
        self.assertIsNone(metrics['barge_totals'][0]['average_tons_per_trip'])
        self.assertEqual(metrics['barge_totals'][0]['status'], 'Trip Data Missing')

    def test_sand_area_status_logic(self):
        SandAreaProgress.objects.create(
            project=self.project,
            area_zone='Zone A',
            planned_quantity_ton=Decimal('1000.00'),
            delivered_quantity_ton=Decimal('700.00'),
            placed_quantity_ton=Decimal('500.00'),
            planned_placed_to_date_ton=Decimal('600.00'),
            placement_type='Offshore',
        )
        SandDailyRecord.objects.create(
            project=self.project,
            record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000.00'),
        )
        recalculate_sand_accumulatives(self.project)

        metrics = get_sand_dashboard_data(self.project)

        self.assertEqual(metrics['area_rows'][0]['completion_percent'], 50.0)
        self.assertEqual(metrics['area_rows'][0]['status'], 'Delayed')


class OrmAggregationTests(TestCase):
    """Verify ORM-aggregated production_days and averages match the previous Python results."""

    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)

    def test_rock_production_days_skips_zero_placement_days(self):
        RockDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('500'), placed_daily_ton=Decimal('400'),
        )
        RockDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 2),
            tct_daily_ton=Decimal('200'), placed_daily_ton=Decimal('0'),
        )
        RockDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 3),
            tct_daily_ton=Decimal('300'), placed_daily_ton=Decimal('300'),
        )
        recalculate_rock_accumulatives(self.project)

        metrics = get_rock_dashboard_data(self.project)

        # Only days 1 and 3 had placement > 0  →  average = (400+300)/2 = 350
        self.assertEqual(metrics['average_daily_placement'], 350.0)
        self.assertEqual(metrics['record_count'], 3)

    def test_rock_no_placement_days_returns_none_average(self):
        RockDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('500'), placed_daily_ton=Decimal('0'),
        )
        recalculate_rock_accumulatives(self.project)

        metrics = get_rock_dashboard_data(self.project)

        self.assertIsNone(metrics['average_daily_placement'])

    def test_sand_delivery_and_placement_days_counted_independently(self):
        # Day 1: delivery only
        SandDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('200'), mtp3_daily_ton=Decimal('0'),
            offshore_daily_ton=Decimal('0'), onshore_daily_ton=Decimal('0'),
        )
        # Day 2: both delivery and placement
        SandDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 2),
            tct_daily_ton=Decimal('300'), mtp3_daily_ton=Decimal('100'),
            offshore_daily_ton=Decimal('150'), onshore_daily_ton=Decimal('50'),
        )
        recalculate_sand_accumulatives(self.project)

        metrics = get_sand_dashboard_data(self.project)

        # Delivery: days 1+2 both have total_daily_ton > 0 → 2 days, total=(200+400)=600, avg=300
        self.assertEqual(metrics['average_daily_delivery'], 300.0)
        # Placement: only day 2 → 1 day, total=200, avg=200
        self.assertEqual(metrics['average_daily_placement'], 200.0)

    def test_sand_no_placement_returns_none_forecast(self):
        SandDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('500'), offshore_daily_ton=Decimal('0'),
        )
        recalculate_sand_accumulatives(self.project)

        metrics = get_sand_dashboard_data(self.project)

        self.assertIsNone(metrics['average_daily_placement'])
        self.assertIsNone(metrics['forecast_completion_date'])


class RockChartDataViewTests(TestCase):
    """Verify RockChartDataView returns correct structure with no N+1 queries."""

    def setUp(self):
        self.user = make_user()
        self.project = make_project(self.user)
        self.client = Client()
        self.client.force_login(self.user)

    def test_chart_data_returns_barge_totals_aggregated(self):
        record = RockDailyRecord.objects.create(
            project=self.project, record_date=date(2026, 5, 1),
            tct_daily_ton=Decimal('1000'), placed_daily_ton=Decimal('900'),
        )
        barge_a = Barge.objects.create(name='Barge Alpha', code='BA')
        barge_b = Barge.objects.create(name='Barge Beta', code='BB')
        RockBargePlacement.objects.create(record=record, barge=barge_a, quantity_ton=Decimal('600'))
        RockBargePlacement.objects.create(record=record, barge=barge_b, quantity_ton=Decimal('300'))
        recalculate_rock_accumulatives(self.project)

        response = self.client.get(
            f'/project-controls/rock/chart-data/?project_id={self.project.pk}'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('barge_totals', data)
        self.assertEqual(data['barge_totals']['Barge Alpha'], 600.0)
        self.assertEqual(data['barge_totals']['Barge Beta'], 300.0)
        self.assertEqual(data['labels'], ['2026-05-01'])
        self.assertEqual(data['daily_delivered'], [1000.0])

    def test_chart_data_missing_project_returns_400(self):
        response = self.client.get('/project-controls/rock/chart-data/')

        self.assertEqual(response.status_code, 400)
