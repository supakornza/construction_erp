from django.contrib import admin
from .models import (
    Barge, RockDailyRecord, RockBargePlacement, RockDashboardSettings, RockStationProgress,
    SandDailyRecord, SandBargePlacement, SandDashboardSettings, SandAreaProgress, SandAllocation,
    RecoveryPlan, RecoveryPlanDailyItem,
    RecoveryActionPlan, RecoveryActionItem, RecoveryActionDailyProgress,
    ProjectActionPlan,
    LogisticsScenario, ImportLog,
    RevetmentStation, RevetmentActivity,
    RevetmentDailyRecord, RevetmentDailyItem,
)


@admin.register(Barge)
class BargeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'transport_mode', 'capacity_ton', 'equipment', 'is_active']
    list_filter = ['transport_mode', 'is_active']
    search_fields = ['name', 'code']
    autocomplete_fields = ['equipment']


class RockBargePlacementInline(admin.TabularInline):
    model = RockBargePlacement
    extra = 1
    fields = ['barge', 'quantity_ton', 'trips', 'placement_type', 'station', 'remarks']


@admin.register(RockDailyRecord)
class RockDailyRecordAdmin(admin.ModelAdmin):
    list_display = ['project', 'record_date', 'tct_daily_ton', 'tct_accum_ton',
                    'placed_daily_ton', 'placed_accum_ton', 'material_type', 'station_of_core']
    list_filter = ['project', 'material_type']
    date_hierarchy = 'record_date'
    search_fields = ['project__contract_no', 'source_quarry', 'destination_area', 'remarks']
    inlines = [RockBargePlacementInline]


@admin.register(RockDashboardSettings)
class RockDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['project', 'target_quantity_ton', 'daily_target_placement_ton',
                    'planned_start_date', 'planned_finish_date', 'updated_at']
    search_fields = ['project__contract_no', 'project__project_name']


@admin.register(RockStationProgress)
class RockStationProgressAdmin(admin.ModelAdmin):
    list_display = ['project', 'station_range', 'material_type', 'delivered_quantity_ton',
                    'placed_quantity_ton', 'target_quantity_ton', 'completion_percent', 'status']
    list_filter = ['project', 'material_type']
    search_fields = ['project__contract_no', 'station_range', 'remarks']


class SandBargePlacementInline(admin.TabularInline):
    model = SandBargePlacement
    extra = 1
    fields = ['barge', 'quantity_ton', 'trips', 'source', 'destination', 'placement_type', 'station', 'status']


@admin.register(SandDailyRecord)
class SandDailyRecordAdmin(admin.ModelAdmin):
    list_display = ['project', 'record_date', 'tct_daily_ton', 'mtp3_daily_ton',
                    'chalothon_daily_ton', 'khlong_bang_phai_daily_ton',
                    'total_daily_ton', 'remaining_tct', 'remaining_mtp3']
    list_filter = ['project']
    date_hierarchy = 'record_date'
    search_fields = ['project__contract_no', 'sand_source', 'remarks']
    inlines = [SandBargePlacementInline]


@admin.register(SandDashboardSettings)
class SandDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['project', 'target_quantity_ton', 'daily_target_delivery_ton',
                    'daily_target_placement_ton', 'planned_start_date', 'planned_finish_date', 'updated_at']
    search_fields = ['project__contract_no', 'project__project_name']


@admin.register(SandAreaProgress)
class SandAreaProgressAdmin(admin.ModelAdmin):
    list_display = ['project', 'area_zone', 'placement_type', 'planned_quantity_ton',
                    'delivered_quantity_ton', 'placed_quantity_ton',
                    'completion_percent', 'status']
    list_filter = ['project', 'placement_type']
    search_fields = ['project__contract_no', 'area_zone', 'remarks']


@admin.register(SandAllocation)
class SandAllocationAdmin(admin.ModelAdmin):
    list_display = ['project', 'calculation_date', 'total_sand_quantity',
                    'tct_percentage', 'mtp3_percentage', 'total_trips']
    list_filter = ['project']


@admin.register(RevetmentStation)
class RevetmentStationAdmin(admin.ModelAdmin):
    list_display = ['project', 'sop', 'station', 'sort_order', 'is_active']
    list_filter = ['project', 'sop', 'is_active']
    search_fields = ['station', 'sop', 'project__contract_no']


@admin.register(RevetmentActivity)
class RevetmentActivityAdmin(admin.ModelAdmin):
    list_display = ['project', 'group_name', 'name', 'unit', 'template_column',
                    'is_inspection', 'sort_order', 'is_active']
    list_filter = ['project', 'group_name', 'is_inspection', 'is_active']
    search_fields = ['group_name', 'name', 'project__contract_no']


class RevetmentDailyItemInline(admin.TabularInline):
    model = RevetmentDailyItem
    extra = 1


@admin.register(RevetmentDailyRecord)
class RevetmentDailyRecordAdmin(admin.ModelAdmin):
    list_display = ['project', 'record_date', 'day_name', 'created_by', 'updated_at']
    list_filter = ['project']
    date_hierarchy = 'record_date'
    search_fields = ['project__contract_no', 'remarks']
    inlines = [RevetmentDailyItemInline]


class RecoveryPlanDailyItemInline(admin.TabularInline):
    model = RecoveryPlanDailyItem
    extra = 0


@admin.register(RecoveryPlan)
class RecoveryPlanAdmin(admin.ModelAdmin):
    list_display = ['plan_name', 'project', 'material_type', 'start_date', 'end_date', 'status']
    list_filter = ['project', 'material_type', 'status']
    inlines = [RecoveryPlanDailyItemInline]


class RecoveryActionItemInline(admin.TabularInline):
    model = RecoveryActionItem
    extra = 0


@admin.register(RecoveryActionPlan)
class RecoveryActionPlanAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'status', 'start_date', 'end_date', 'prepared_by']
    list_filter = ['project', 'status']
    inlines = [RecoveryActionItemInline]


class RecoveryActionDailyProgressInline(admin.TabularInline):
    model = RecoveryActionDailyProgress
    extra = 0


@admin.register(RecoveryActionItem)
class RecoveryActionItemAdmin(admin.ModelAdmin):
    list_display = ['item_no', 'description', 'total_quantity', 'unit', 'recovery_plan']
    list_filter = ['recovery_plan__project']
    inlines = [RecoveryActionDailyProgressInline]


@admin.register(ProjectActionPlan)
class ProjectActionPlanAdmin(admin.ModelAdmin):
    list_display = ['action_id', 'project', 'description_th', 'responsible_parties',
                    'due_date', 'priority', 'status', 'category', 'meeting_reference']
    list_filter = ['project', 'category', 'priority', 'status']
    search_fields = [
        'action_id', 'description_th', 'responsible_parties', 'meeting_reference',
        'remarks', 'project__contract_no', 'project__project_name',
    ]
    date_hierarchy = 'date_raised'


@admin.register(LogisticsScenario)
class LogisticsScenarioAdmin(admin.ModelAdmin):
    list_display = ['scenario_name', 'project', 'material_type', 'number_of_trucks',
                    'truck_capacity_ton', 'working_hours']
    list_filter = ['project', 'material_type']


@admin.register(ImportLog)
class ImportLogAdmin(admin.ModelAdmin):
    list_display = ['project', 'import_type', 'status', 'total_rows',
                    'success_rows', 'failed_rows', 'imported_by', 'imported_at']
    list_filter = ['project', 'import_type', 'status']
    readonly_fields = ['imported_at']
