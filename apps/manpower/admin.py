from django.contrib import admin
from .models import ManpowerCategory, DailyManpowerRecord


@admin.register(ManpowerCategory)
class ManpowerCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(DailyManpowerRecord)
class DailyManpowerRecordAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'project', 'category', 'company', 'quantity']
    list_filter = ['category', 'project']
    search_fields = ['company', 'project__project_name']
    date_hierarchy = 'report_date'
