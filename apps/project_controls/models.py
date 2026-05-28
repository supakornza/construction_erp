import math
import re
from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.accounts.models import User
from apps.projects.models import Project


# ── Reference ─────────────────────────────────────────────────────────────────

class Barge(models.Model):
    TRANSPORT_OFFSHORE = 'Offshore'
    TRANSPORT_ONSHORE = 'Onshore'
    TRANSPORT_BOTH = 'Both'
    TRANSPORT_MODE_CHOICES = [
        (TRANSPORT_OFFSHORE, 'Offshore'),
        (TRANSPORT_ONSHORE, 'Onshore'),
        (TRANSPORT_BOTH, 'Both'),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    transport_mode = models.CharField(max_length=20, choices=TRANSPORT_MODE_CHOICES, default=TRANSPORT_OFFSHORE)
    capacity_ton = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    equipment = models.ForeignKey(
        'equipment.Equipment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='transport_units',
        help_text='Link to Equipment record (optional)',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


# ── Rock ──────────────────────────────────────────────────────────────────────

class RockDailyRecord(models.Model):
    MATERIAL_CORE = 'Core Rock'
    MATERIAL_BEDDING = 'Bedding Rock'
    MATERIAL_ARMOUR = 'Armour Rock'
    MATERIAL_TOE = 'Toe Rock'
    MATERIAL_QUARRY_RUN = 'Quarry Run'
    ROCK_MATERIAL_CHOICES = [
        (MATERIAL_CORE, 'Core Rock'),
        (MATERIAL_BEDDING, 'Bedding Rock'),
        (MATERIAL_ARMOUR, 'Armour Rock'),
        (MATERIAL_TOE, 'Toe Rock'),
        (MATERIAL_QUARRY_RUN, 'Quarry Run'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rock_daily_records')
    record_date = models.DateField()
    day_name = models.CharField(max_length=10, blank=True)
    material_type = models.CharField(max_length=30, choices=ROCK_MATERIAL_CHOICES, blank=True)
    source_quarry = models.CharField(max_length=200, blank=True)
    destination_area = models.CharField(max_length=200, blank=True)

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
        indexes = [
            models.Index(fields=['project', '-record_date'], name='rock_project_date_idx'),
        ]

    def __str__(self):
        return f"{self.project.contract_no} Rock – {self.record_date}"

    @property
    def stock_balance(self):
        return self.tct_accum_ton - self.placed_accum_ton


class RockDashboardSettings(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='rock_dashboard_settings')
    target_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    daily_target_placement_ton = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_finish_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Rock Dashboard Settings'

    def __str__(self):
        return f'{self.project.contract_no} Rock Dashboard Settings'


class RockBargePlacement(models.Model):
    PLACEMENT_OFFSHORE = 'Offshore'
    PLACEMENT_ONSHORE = 'Onshore'
    PLACEMENT_CHOICES = [
        (PLACEMENT_OFFSHORE, 'Offshore'),
        (PLACEMENT_ONSHORE, 'Onshore'),
    ]

    record = models.ForeignKey(RockDailyRecord, on_delete=models.CASCADE, related_name='barge_placements')
    barge = models.ForeignKey('equipment.Equipment', on_delete=models.SET_NULL, null=True, blank=True)
    quantity_ton = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trips = models.IntegerField(null=True, blank=True)
    placement_type = models.CharField(max_length=20, choices=PLACEMENT_CHOICES, default=PLACEMENT_OFFSHORE)
    station = models.CharField(max_length=300, blank=True)
    remarks = models.CharField(max_length=300, blank=True)

    class Meta:
        unique_together = ('record', 'barge')
        ordering = ['barge__name']

    def __str__(self):
        barge_name = self.barge.name if self.barge_id else '—'
        return f"{self.record} – {barge_name}: {self.quantity_ton}T"


# ── Sand ──────────────────────────────────────────────────────────────────────

class RockStationProgress(models.Model):
    STATUS_COMPLETED = 'Completed'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_NOT_STARTED = 'Not Started'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='rock_station_progress')
    station_range = models.CharField(max_length=100)
    material_type = models.CharField(
        max_length=30,
        choices=RockDailyRecord.ROCK_MATERIAL_CHOICES,
        default=RockDailyRecord.MATERIAL_CORE,
    )
    delivered_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    placed_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    target_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    remarks = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['station_range', 'material_type']
        unique_together = ('project', 'station_range', 'material_type')

    def __str__(self):
        return f'{self.project.contract_no} {self.station_range} {self.material_type}'

    @property
    def completion_percent(self):
        denominator = self.target_quantity_ton or self.delivered_quantity_ton
        if denominator and denominator > 0:
            return round(float(self.placed_quantity_ton) / float(denominator) * 100, 1)
        return 0

    @property
    def status(self):
        pct = self.completion_percent
        if pct >= 100:
            return self.STATUS_COMPLETED
        if pct > 0:
            return self.STATUS_IN_PROGRESS
        return self.STATUS_NOT_STARTED


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

    chalothon_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    chalothon_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    chalothon_trips = models.IntegerField(default=0)
    chalothon_trucks = models.IntegerField(default=0)

    khlong_bang_phai_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    khlong_bang_phai_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    khlong_bang_phai_trips = models.IntegerField(default=0)
    khlong_bang_phai_trucks = models.IntegerField(default=0)

    oswald_daily_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    oswald_accum_ton = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    oswald_trips = models.IntegerField(default=0)
    oswald_trucks = models.IntegerField(default=0)
    sand_source = models.CharField(max_length=200, default='Khlong Bang Phai (Oswald)', blank=True)

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
        indexes = [
            models.Index(fields=['project', '-record_date'], name='sand_project_date_idx'),
        ]

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
        return self.sand_source or 'Khlong Bang Phai (Oswald)'

    @property
    def tct_destination_label(self):
        return 'TCT Pier'

    @property
    def mtp3_destination_label(self):
        return 'Stockpile Sand MTP3'

    @property
    def total_source_daily_ton(self):
        return self.chalothon_daily_ton + self.khlong_bang_phai_daily_ton

    @property
    def total_source_accum_ton(self):
        return self.chalothon_accum_ton + self.khlong_bang_phai_accum_ton


class SandBargePlacement(models.Model):
    PLACEMENT_OFFSHORE = 'Offshore'
    PLACEMENT_ONSHORE = 'Onshore'
    PLACEMENT_CHOICES = [
        (PLACEMENT_OFFSHORE, 'Offshore'),
        (PLACEMENT_ONSHORE, 'Onshore'),
    ]

    STATUS_RECORDED = 'Recorded'
    STATUS_MISSING_TRIPS = 'Trip Data Missing'
    STATUS_CHOICES = [
        (STATUS_RECORDED, 'Recorded'),
        (STATUS_MISSING_TRIPS, 'Trip Data Missing'),
    ]

    record = models.ForeignKey(SandDailyRecord, on_delete=models.CASCADE, related_name='barge_placements')
    barge = models.ForeignKey('equipment.Equipment', on_delete=models.SET_NULL, null=True, blank=True)
    quantity_ton = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    trips = models.IntegerField(null=True, blank=True)
    station = models.CharField(max_length=300, blank=True)
    source = models.CharField(max_length=200, blank=True)
    destination = models.CharField(max_length=200, blank=True)
    placement_type = models.CharField(max_length=20, choices=PLACEMENT_CHOICES, default=PLACEMENT_OFFSHORE)
    material_type = models.CharField(max_length=50, default='Sand', blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_RECORDED)

    class Meta:
        unique_together = ('record', 'barge')
        ordering = ['barge__name']

    def __str__(self):
        barge_name = self.barge.name if self.barge_id else '—'
        return f"{self.record} – {barge_name}: {self.quantity_ton}T"


# ── Sand Allocation ───────────────────────────────────────────────────────────

class SandDashboardSettings(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='sand_dashboard_settings')
    target_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    daily_target_delivery_ton = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    daily_target_placement_ton = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    planned_start_date = models.DateField(null=True, blank=True)
    planned_finish_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Sand Dashboard Settings'

    def __str__(self):
        return f'{self.project.contract_no} Sand Dashboard Settings'


class SandAreaProgress(models.Model):
    STATUS_COMPLETED = 'Completed'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_NOT_STARTED = 'Not Started'
    STATUS_DELAYED = 'Delayed'

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sand_area_progress')
    area_zone = models.CharField(max_length=120)
    planned_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    delivered_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    placed_quantity_ton = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_placed_to_date_ton = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    placement_type = models.CharField(
        max_length=20,
        choices=SandBargePlacement.PLACEMENT_CHOICES,
        blank=True,
    )
    remarks = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['area_zone', 'placement_type']
        unique_together = ('project', 'area_zone', 'placement_type')

    def __str__(self):
        return f'{self.project.contract_no} {self.area_zone}'

    @property
    def remaining_quantity_ton(self):
        if self.planned_quantity_ton is None:
            return None
        remaining = self.planned_quantity_ton - self.placed_quantity_ton
        return remaining if remaining > 0 else Decimal('0')

    @property
    def completion_percent(self):
        if self.planned_quantity_ton and self.planned_quantity_ton > 0:
            return round(float(self.placed_quantity_ton) / float(self.planned_quantity_ton) * 100, 1)
        return 0

    @property
    def status(self):
        if self.planned_placed_to_date_ton and self.placed_quantity_ton < self.planned_placed_to_date_ton:
            return self.STATUS_DELAYED
        pct = self.completion_percent
        if pct >= 100:
            return self.STATUS_COMPLETED
        if pct > 0:
            return self.STATUS_IN_PROGRESS
        return self.STATUS_NOT_STARTED


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
        indexes = [
            models.Index(fields=['project', '-record_date'], name='revetment_project_date_idx'),
        ]

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

    @property
    def total_plan(self):
        return self.total_planned

    @property
    def total_deviation(self):
        return self.total_actual - self.total_planned

    @property
    def achievement_pct(self):
        return self.achievement_percent


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
    def plan_quantity(self):
        return self.planned_quantity

    @property
    def plan_accum(self):
        return self.accumulative_planned

    @property
    def actual_accum(self):
        return self.accumulative_actual

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

class ProjectActionPlan(models.Model):
    CATEGORY_CHOICES = [
        ('Technical', 'Technical'),
        ('Documentation', 'Documentation'),
        ('Regulatory', 'Regulatory'),
        ('Safety', 'Safety'),
        ('Site Management', 'Site Management'),
        ('Security', 'Security'),
        ('Coordination', 'Coordination'),
        ('Commercial', 'Commercial'),
        ('Other', 'Other'),
    ]
    PRIORITY_CHOICES = [
        ('High', 'High'),
        ('Medium', 'Medium'),
        ('Low', 'Low'),
        ('Critical', 'Critical'),
    ]
    STATUS_OPEN = 'Open'
    STATUS_IN_PROGRESS = 'In Progress'
    STATUS_PENDING = 'Pending'
    STATUS_FINISH = 'Finish'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING, 'Pending'),
        (STATUS_FINISH, 'Finish'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    CLOSED_STATUSES = {STATUS_FINISH, STATUS_CANCELLED}

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='project_action_plans')
    action_id = models.CharField(max_length=20, blank=True)
    date_raised = models.DateField(default=timezone.localdate)
    description_th = models.TextField(blank=True)
    responsible_parties = models.CharField(max_length=300, blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='Other')
    meeting_reference = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='project_action_plans_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['action_id']
        unique_together = ('project', 'action_id')
        indexes = [
            models.Index(fields=['project', 'status', 'due_date'], name='pm_ap_project_status_idx'),
        ]

    def __str__(self):
        return f"{self.action_id} - {self.description_th[:80]}"

    def save(self, *args, **kwargs):
        if not self.action_id and self.project_id:
            self.action_id = self.next_action_id(self.project_id)
        super().save(*args, **kwargs)

    @classmethod
    def next_action_id(cls, project_id):
        max_number = 0
        for action_id in cls.objects.filter(project_id=project_id).values_list('action_id', flat=True):
            match = re.fullmatch(r'ACT-(\d+)', action_id or '')
            if match:
                max_number = max(max_number, int(match.group(1)))
        return f'ACT-{max_number + 1:03d}'

    @property
    def is_overdue(self):
        return bool(
            self.due_date
            and self.due_date < timezone.localdate()
            and self.status not in self.CLOSED_STATUSES
        )

    @property
    def responsible_party_list(self):
        return [party.strip() for party in self.responsible_parties.split(',') if party.strip()]


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
