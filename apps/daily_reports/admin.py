from django.contrib import admin
from .models import DailyReport, DailyWorkActivity, DailyLookahead, DailyProblemRemark, DailyPhoto


class DailyWorkActivityInline(admin.TabularInline):
    model = DailyWorkActivity
    extra = 1


class DailyLookaheadInline(admin.TabularInline):
    model = DailyLookahead
    extra = 1


class DailyProblemRemarkInline(admin.TabularInline):
    model = DailyProblemRemark
    extra = 1


class DailyPhotoInline(admin.TabularInline):
    model = DailyPhoto
    extra = 1


@admin.register(DailyReport)
class DailyReportAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'project', 'status', 'prepared_by', 'weather_morning', 'created_at']
    list_filter = ['status', 'project', 'weather_morning']
    search_fields = ['project__project_name', 'project__contract_no']
    date_hierarchy = 'report_date'
    inlines = [DailyWorkActivityInline, DailyLookaheadInline, DailyProblemRemarkInline, DailyPhotoInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DailyProblemRemark)
class DailyProblemRemarkAdmin(admin.ModelAdmin):
    list_display = ['report', 'category', 'status', 'description']
    list_filter = ['category', 'status']
    search_fields = ['description']
