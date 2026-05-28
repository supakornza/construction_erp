from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('',                                  views.MaintenanceDashboardView.as_view(), name='dashboard'),
    # PM Schedules
    path('schedules/',                        views.ScheduleListView.as_view(),         name='schedule_list'),
    path('schedules/create/',                 views.ScheduleCreateView.as_view(),       name='schedule_create'),
    path('schedules/<int:pk>/edit/',         views.ScheduleUpdateView.as_view(),       name='schedule_update'),
    # Work Orders
    path('work-orders/',                      views.WorkOrderListView.as_view(),        name='wo_list'),
    path('work-orders/create/',               views.WorkOrderCreateView.as_view(),      name='wo_create'),
    path('work-orders/<int:pk>/',            views.WorkOrderDetailView.as_view(),      name='wo_detail'),
    path('work-orders/<int:pk>/edit/',       views.WorkOrderUpdateView.as_view(),      name='wo_update'),
    path('work-orders/<int:pk>/start/',      views.WorkOrderStartView.as_view(),       name='wo_start'),
    path('work-orders/<int:pk>/complete/',   views.WorkOrderCompleteView.as_view(),    name='wo_complete'),
    path('work-orders/<int:pk>/cancel/',     views.WorkOrderCancelView.as_view(),      name='wo_cancel'),
]
