from django.contrib import admin
from .models import MaintenanceSchedule, MaintenanceWorkOrder, MaintenancePart


class MaintenancePartInline(admin.TabularInline):
    model = MaintenancePart
    extra = 0


@admin.register(MaintenanceSchedule)
class MaintenanceScheduleAdmin(admin.ModelAdmin):
    list_display  = ['equipment', 'title', 'work_type', 'interval_value',
                     'interval_type', 'last_done_date', 'next_due_date', 'is_active']
    list_filter   = ['work_type', 'interval_type', 'is_active']
    search_fields = ['title', 'equipment__name']


@admin.register(MaintenanceWorkOrder)
class MaintenanceWorkOrderAdmin(admin.ModelAdmin):
    list_display  = ['wo_no', 'equipment', 'title', 'work_type',
                     'priority', 'status', 'planned_date']
    list_filter   = ['status', 'work_type', 'priority']
    search_fields = ['wo_no', 'title', 'equipment__name']
    inlines       = [MaintenancePartInline]
