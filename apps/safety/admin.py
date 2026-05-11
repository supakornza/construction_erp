from django.contrib import admin
from .models import ToolboxMeeting, SafetyInspection, IncidentReport, JSEARecord


@admin.register(ToolboxMeeting)
class ToolboxMeetingAdmin(admin.ModelAdmin):
    list_display = ['meeting_date', 'project', 'topic', 'conducted_by', 'attendee_count']
    list_filter = ['project']
    search_fields = ['topic', 'location']
    date_hierarchy = 'meeting_date'


@admin.register(SafetyInspection)
class SafetyInspectionAdmin(admin.ModelAdmin):
    list_display = ['inspection_date', 'project', 'category', 'status', 'responsible_person', 'due_date']
    list_filter = ['status', 'project']
    search_fields = ['category', 'finding']
    date_hierarchy = 'inspection_date'


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ['incident_date', 'project', 'type', 'status', 'reported_by']
    list_filter = ['type', 'status', 'project']
    search_fields = ['description', 'injured_person']
    date_hierarchy = 'incident_date'


@admin.register(JSEARecord)
class JSEARecordAdmin(admin.ModelAdmin):
    list_display = ['date', 'project', 'work_activity', 'prepared_by', 'approved_by']
    list_filter = ['project']
    search_fields = ['work_activity', 'work_area']
    date_hierarchy = 'date'
