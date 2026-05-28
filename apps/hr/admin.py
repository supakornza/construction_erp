from django.contrib import admin
from .models import Employee, AttendanceRecord, LeaveRequest, OvertimeRequest


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display  = ['employee_no', 'full_name', 'company', 'position', 'project', 'status']
    list_filter   = ['status', 'employment_type', 'nationality', 'project']
    search_fields = ['first_name', 'last_name', 'employee_no', 'company']


@admin.register(AttendanceRecord)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'record_date', 'status', 'time_in', 'time_out', 'overtime_hours']
    list_filter  = ['status', 'record_date', 'project']
    date_hierarchy = 'record_date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'days', 'status']
    list_filter  = ['status', 'leave_type']


@admin.register(OvertimeRequest)
class OvertimeRequestAdmin(admin.ModelAdmin):
    list_display = ['employee', 'ot_date', 'planned_hours', 'actual_hours', 'status']
    list_filter  = ['status', 'project']
