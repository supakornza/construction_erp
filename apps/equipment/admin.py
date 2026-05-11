from django.contrib import admin
from .models import EquipmentCategory, Equipment, DailyEquipmentRecord


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'registration_no', 'project', 'status']
    list_filter = ['category', 'status', 'project']
    search_fields = ['name', 'registration_no']


@admin.register(DailyEquipmentRecord)
class DailyEquipmentRecordAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'project', 'equipment', 'status', 'working_hours']
    list_filter = ['status', 'project']
    search_fields = ['equipment__name']
    date_hierarchy = 'report_date'
