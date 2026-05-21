from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('',                                  views.HRDashboardView.as_view(),          name='dashboard'),
    # Employees
    path('employees/',                        views.EmployeeListView.as_view(),          name='employee_list'),
    path('employees/create/',                 views.EmployeeCreateView.as_view(),        name='employee_create'),
    path('employees/<int:pk>/',              views.EmployeeDetailView.as_view(),        name='employee_detail'),
    path('employees/<int:pk>/edit/',         views.EmployeeUpdateView.as_view(),        name='employee_update'),
    # Attendance
    path('attendance/',                       views.AttendanceDashboardView.as_view(),   name='attendance_dashboard'),
    path('attendance/save/',                  views.AttendanceQuickSaveView.as_view(),   name='attendance_save'),
    path('attendance/create/',               views.AttendanceRecordCreateView.as_view(),name='attendance_create'),
    path('attendance/<int:pk>/edit/',        views.AttendanceRecordUpdateView.as_view(),name='attendance_update'),
    # Leave
    path('leave/',                            views.LeaveListView.as_view(),             name='leave_list'),
    path('leave/create/',                     views.LeaveRequestCreateView.as_view(),    name='leave_create'),
    path('leave/<int:pk>/',                  views.LeaveRequestDetailView.as_view(),    name='leave_detail'),
    path('leave/<int:pk>/approve/',          views.LeaveApproveView.as_view(),          name='leave_approve'),
    path('leave/<int:pk>/reject/',           views.LeaveRejectView.as_view(),           name='leave_reject'),
    # Overtime
    path('overtime/',                         views.OvertimeListView.as_view(),          name='ot_list'),
    path('overtime/create/',                  views.OvertimeRequestCreateView.as_view(), name='ot_create'),
    path('overtime/<int:pk>/approve/',       views.OvertimeApproveView.as_view(),       name='ot_approve'),
    path('overtime/<int:pk>/reject/',        views.OvertimeRejectView.as_view(),        name='ot_reject'),
]
