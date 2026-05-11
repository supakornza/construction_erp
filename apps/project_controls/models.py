import math
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.projects.models import Project


# ── Reference ─────────────────────────────────────────────────────────────────

class Barge(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    capacity_ton = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ── Rock ──────────────────────────────────────────────────────────────────────

class RockDailyRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rock_daily_records')
    record_date = models.DateField()
    day_name = models.CharField(max_length=10, blank=True)

    tct_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tct_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tct_trips = models.IntegerField(default=0)
    tct_trucks = models.IntegerField(default=0)

    placed_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    placed_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    station_of_core = models.CharField(max_length=300, blank=True)

    core_outside_daily = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    core_outside_accum = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    core_inside_accum = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='rock_records_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'record_date')
        ordering = ['-record_date']

    def __str__(self):
        return f"{self.project.contract_no} Rock – {self.record_date}"

    @property
    def stock_balance(self):
        return self.tct_accum_ton - self.placed_accum_ton


class RockBargePlacement(models.Model):
    record = models.ForeignKey(RockDailyRecord, on_delete=models.CASCADE, related_name='barge_placements')
    barge = models.ForeignKey(Barge, on_delete=models.PROTECT)
    quantity_ton = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trips = models.IntegerField(default=0)
    station = models.CharField(max_length=300, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ('record', 'barge')
        ordering = ['barge__name']

    def __str__(self):
        return f"{self.record} – {self.barge.name}: {self.quantity_ton}T"


# ── Sand ──────────────────────────────────────────────────────────────────────

class SandDailyRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sand_daily_records')
    record_date = models.DateField()
    day_name = models.CharField(max_length=10, blank=True)

    tct_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tct_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tct_trips = models.IntegerField(default=0)
    tct_trucks = models.IntegerField(default=0)

    mtp3_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mtp3_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mtp3_trips = models.IntegerField(default=0)
    mtp3_trucks = models.IntegerField(default=0)

    oswald_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    oswald_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    oswald_trips = models.IntegerField(default=0)
    oswald_trucks = models.IntegerField(default=0)
    sand_source = models.CharField(max_length=200, default='Oswald', blank=True)

    total_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    offshore_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    offshore_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    offshore_station = models.CharField(max_length=300, blank=True)

    onshore_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    onshore_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    onshore_trips = models.IntegerField(default=0)
    onshore_trucks = models.IntegerField(default=0)
    inplace_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    inside_plot_daily = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    inside_plot_accum = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    outside_plot_daily = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outside_plot_accum = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    remaining_tct = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_mtp3 = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='sand_records_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'record_date')
        ordering = ['-record_date']

    def __str__(self):
        return f"{self.project.contract_no} Sand – {self.record_date}"

    @property
    def total_remaining(self):
        return self.remaining_tct + self.remaining_mtp3

    @property
    def total_placed(self):
        return self.offshore_accum_ton + self.onshore_accum_ton

    @property
    def sand_source_display(self):
        return self.sand_source or 'Other source'


class SandBargePlacement(models.Model):
    record = models.ForeignKey(SandDailyRecord, on_delete=models.CASCADE, related_name='barge_placements')
    barge = models.ForeignKey(Barge, on_delete=models.PROTECT)
    quantity_ton = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trips = models.IntegerField(default=0)
    station = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ('record', 'barge')
        ordering = ['barge__name']

    def __str__(self):
        return f"{self.record} – {self.barge.name}: {self.quantity_ton}T"


# ── Sand Allocation ───────────────────────────────────────────────────────────

class SandAllocation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sand_allocations')
    calculation_date = models.DateField(default=timezone.now)
    total_sand_quantity = models.DecimalField(max_digits=15, decimal_places=2)
    tct_percentage = models.DecimalField(max_digits=5, decimal_places=3,
                                         help_text='Decimal 0–1, e.g. 0.464 = 46.4%')
    mtp3_percentage = models.DecimalField(max_digits=5, decimal_places=3,
                                          help_text='Decimal 0–1, e.g. 0.536 = 53.6%')
    total_trips = models.IntegerField()
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='sand_allocations_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calculation_date']

    def __str__(self):
        return f"{self.project.contract_no} Allocation – {self.calculation_date}"

    def clean(self):
        if self.tct_percentage is not None and self.mtp3_percentage is not None:
            total = self.tct_percentage + self.mtp3_percentage
            if abs(total - Decimal('1.0')) > Decimal('0.001'):
                raise ValidationError('TCT % + MTP3 % must equal 1.0 (100%)')
        if self.total_trips is not None and self.total_trips <= 0:
            raise ValidationError('Total trips must be positive')

    @property
    def calculated_tct_quantity(self):
        return round(self.total_sand_quantity * self.tct_percentage, 2)

    @property
    def calculated_mtp3_quantity(self):
        return round(self.total_sand_quantity * self.mtp3_percentage, 2)

    @property
    def calculated_tct_trips(self):
        return round(self.total_trips * float(self.tct_percentage))

    @property
    def calculated_mtp3_trips(self):
        return self.total_trips - self.calculated_tct_trips


# ── 14-Day Recovery Plan ──────────────────────────────────────────────────────

class RevetmentStation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='revetment_stations')
    sop = models.CharField(max_length=50, blank=True)
    station = models.CharField(max_length=30)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'station']
        unique_together = ('project', 'station')

    def __str__(self):
        prefix = f'{self.sop} - ' if self.sop else ''
        return f'{self.project.contract_no} - {prefix}{self.station}'


class RevetmentActivity(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='revetment_activities')
    group_name = models.CharField(max_length=120, blank=True)
    name = models.CharField(max_length=120)
    template_column = models.CharField(max_length=5, blank=True)
    unit = models.CharField(max_length=30, blank=True)
    is_inspection = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'group_name', 'name']
        unique_together = ('project', 'template_column', 'name')

    def __str__(self):
        group = f'{self.group_name} - ' if self.group_name else ''
        return f'{self.project.contract_no} - {group}{self.name}'

    @property
    def display_unit(self):
        if self.is_inspection:
            return self.unit or 'status'
        return self.unit or '-'


class RevetmentDailyRecord(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='revetment_daily_records')
    record_date = models.DateField()
    day_name = models.CharField(max_length=10, blank=True)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='revetment_records_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'record_date')
        ordering = ['-record_date']

    def __str__(self):
        return f'{self.project.contract_no} Revetment - {self.record_date}'

    @property
    def total_quantity(self):
        return self.items.aggregate(total=models.Sum('quantity_done'))['total'] or Decimal('0')


class RevetmentDailyItem(models.Model):
    STATUS_CHOICES = [
        ('Opening', 'Opening'),
        ('Ongoing', 'Ongoing'),
        ('Finished', 'Finished'),
        ('Inspected', 'Inspected'),
        ('No Activity', 'No Activity'),
    ]
    record = models.ForeignKey(RevetmentDailyRecord, on_delete=models.CASCADE, related_name='items')
    station = models.ForeignKey(RevetmentStation, on_delete=models.PROTECT, related_name='daily_items')
    activity = models.ForeignKey(RevetmentActivity, on_delete=models.PROTECT, related_name='daily_items')
    quantity_done = models.DecimalField(max_digits=15, decimal_places=3, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, blank=True)
    inspection_date = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['station__sort_order', 'activity__sort_order']
        unique_together = ('record', 'station', 'activity')

    def __str__(self):
        return f'{self.record} - {self.station.station} - {self.activity.name}'

    def clean(self):
        if self.record_id:
            if self.station_id and self.station.project_id != self.record.project_id:
                raise ValidationError('Station must belong to the same project as the record.')
            if self.activity_id and self.activity.project_id != self.record.project_id:
                raise ValidationError('Activity must belong to the same project as the record.')

    @property
    def display_value(self):
        if self.activity.is_inspection:
            if self.inspection_date:
                return self.inspection_date
            return self.status or '-'
        if self.quantity_done is not None:
            unit = f' {self.activity.unit}' if self.activity.unit else ''
            return f'{self.quantity_done}{unit}'
        return self.status or '-'


class RecoveryPlan(models.Model):
    MATERIAL_CHOICES = [('Sand', 'Sand'), ('Rock', 'Rock'), ('Both', 'Both')]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
        ('Superseded', 'Superseded'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='recovery_plans')
    plan_name = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    material_type = models.CharField(max_length=10, choices=MATERIAL_CHOICES)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='recovery_plans_prepared')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='recovery_plans_approved')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.plan_name} ({self.material_type})"

    @property
    def total_planned(self):
        return self.daily_items.aggregate(t=models.Sum('planned_quantity'))['t'] or Decimal('0')

    @property
    def total_actual(self):
        return self.daily_items.aggregate(t=models.Sum('actual_quantity'))['t'] or Decimal('0')

    @property
    def achievement_percent(self):
        if self.total_planned > 0:
            return round(float(self.total_actual) / float(self.total_planned) * 100, 1)
        return 0


class RecoveryPlanDailyItem(models.Model):
    recovery_plan = models.ForeignKey(RecoveryPlan, on_delete=models.CASCADE, related_name='daily_items')
    plan_date = models.DateField()
    day_name = models.CharField(max_length=10, blank=True)
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_quantity = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    accumulative_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulative_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ('recovery_plan', 'plan_date')
        ordering = ['plan_date']

    def __str__(self):
        return f"{self.recovery_plan.plan_name} – {self.plan_date}"

    @property
    def deviation(self):
        return self.accumulative_actual - self.accumulative_planned

    @property
    def achievement_percent(self):
        if self.planned_quantity and self.planned_quantity > 0 and self.actual_quantity:
            return round(float(self.actual_quantity) / float(self.planned_quantity) * 100, 1)
        return 0


# ── Recovery Action Plan ──────────────────────────────────────────────────────

class RecoveryActionPlan(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Submitted', 'Submitted'),
        ('Reviewed', 'Reviewed'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='recovery_action_plans')
    title = models.CharField(max_length=300)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    prepared_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='rap_prepared')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='rap_approved')
    remarks = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} [{self.status}]"

    @property
    def overall_percent_complete(self):
        items = self.items.all()
        if not items:
            return 0
        pcts = [i.percent_complete for i in items]
        return round(sum(pcts) / len(pcts), 1)


class RecoveryActionItem(models.Model):
    recovery_plan = models.ForeignKey(RecoveryActionPlan, on_delete=models.CASCADE, related_name='items')
    item_no = models.CharField(max_length=10)
    description = models.CharField(max_length=500)
    total_quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit = models.CharField(max_length=50)
    ntp_reference = models.CharField(max_length=200, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        ordering = ['item_no']
        unique_together = ('recovery_plan', 'item_no')

    def __str__(self):
        return f"{self.item_no}. {self.description[:60]}"

    @property
    def total_planned(self):
        return self.daily_progress.aggregate(t=models.Sum('planned_quantity'))['t'] or Decimal('0')

    @property
    def total_actual(self):
        return self.daily_progress.aggregate(t=models.Sum('actual_quantity'))['t'] or Decimal('0')

    @property
    def remaining_quantity(self):
        return self.total_quantity - self.total_actual

    @property
    def percent_complete(self):
        if self.total_quantity > 0:
            return round(float(self.total_actual) / float(self.total_quantity) * 100, 1)
        return 0

    @property
    def latest_status(self):
        p = self.daily_progress.order_by('-progress_date').first()
        return p.status if p else 'No Activity'


class RecoveryActionDailyProgress(models.Model):
    STATUS_CHOICES = [
        ('Ahead', 'Ahead'),
        ('On Track', 'On Track'),
        ('Delayed', 'Delayed'),
        ('No Activity', 'No Activity'),
    ]
    action_item = models.ForeignKey(RecoveryActionItem, on_delete=models.CASCADE, related_name='daily_progress')
    progress_date = models.DateField()
    planned_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulative_planned = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    accumulative_actual = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='No Activity')
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ('action_item', 'progress_date')
        ordering = ['progress_date']

    def __str__(self):
        return f"{self.action_item.item_no} – {self.progress_date}"

    @property
    def deviation(self):
        return self.accumulative_actual - self.accumulative_planned

    @property
    def percent_complete(self):
        total_qty = self.action_item.total_quantity
        if total_qty > 0:
            return round(float(self.accumulative_actual) / float(total_qty) * 100, 1)
        return 0

    def compute_status(self):
        if self.planned_quantity == 0 and self.actual_quantity == 0:
            return 'No Activity'
        dev = self.deviation
        if dev > Decimal('0'):
            return 'Ahead'
        if dev == Decimal('0'):
            return 'On Track'
        return 'Delayed'


# ── Logistics Scenario ────────────────────────────────────────────────────────

class LogisticsScenario(models.Model):
    MATERIAL_CHOICES = [('Sand', 'Sand'), ('Rock', 'Rock')]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='logistics_scenarios')
    scenario_name = models.CharField(max_length=200)
    material_type = models.CharField(max_length=10, choices=MATERIAL_CHOICES)
    number_of_trucks = models.IntegerField(default=20)
    truck_capacity_ton = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('15'))
    route_distance_km = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('16.2'))
    average_speed_kmph = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('60'))
    loading_time_min = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('10'))
    unloading_time_min = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal('5'))
    allowed_start_time_1 = models.TimeField(default='09:00')
    allowed_end_time_1 = models.TimeField(default='15:30')
    allowed_start_time_2 = models.TimeField(null=True, blank=True)
    allowed_end_time_2 = models.TimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('12'))
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='logistics_scenarios_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.scenario_name} – {self.material_type}"

    @property
    def one_way_travel_time_min(self):
        return round(float(self.route_distance_km) / float(self.average_speed_kmph) * 60, 2)

    @property
    def round_trip_travel_time_min(self):
        return round(self.one_way_travel_time_min * 2, 2)

    @property
    def cycle_time_min(self):
        return round(self.round_trip_travel_time_min + float(self.loading_time_min) + float(self.unloading_time_min), 2)

    @property
    def total_working_minutes(self):
        return float(self.working_hours) * 60

    @property
    def trips_per_truck_per_day(self):
        if self.cycle_time_min > 0:
            return math.floor(self.total_working_minutes / self.cycle_time_min)
        return 0

    @property
    def total_trips_per_day(self):
        return self.trips_per_truck_per_day * self.number_of_trucks

    @property
    def total_tonnage_per_day(self):
        return round(self.total_trips_per_day * float(self.truck_capacity_ton), 2)


# ── Import Log ────────────────────────────────────────────────────────────────

class ImportLog(models.Model):
    IMPORT_TYPE_CHOICES = [
        ('rock_summary', 'Rock Summary'),
        ('sand_summary', 'Sand Summary'),
        ('recovery_action_plan', 'Recovery Action Plan'),
        ('revetment_progress', 'Revetment Progress'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='import_logs')
    import_type = models.CharField(max_length=30, choices=IMPORT_TYPE_CHOICES)
    file = models.FileField(upload_to='import_logs/%Y/%m/')
    imported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='import_logs_created')
    imported_at = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    success_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-imported_at']

    def __str__(self):
        return f"{self.get_import_type_display()} – {self.imported_at:%Y-%m-%d %H:%M} [{self.status}]"
