from django.urls import path
from . import views

app_name = 'safety'

urlpatterns = [
    path('toolbox/', views.ToolboxMeetingListView.as_view(), name='toolbox_list'),
    path('toolbox/create/', views.ToolboxMeetingCreateView.as_view(), name='toolbox_create'),
    path('toolbox/<int:pk>/edit/', views.ToolboxMeetingUpdateView.as_view(), name='toolbox_update'),
    path('inspections/', views.SafetyInspectionListView.as_view(), name='inspection_list'),
    path('inspections/create/', views.SafetyInspectionCreateView.as_view(), name='inspection_create'),
    path('inspections/<int:pk>/', views.SafetyInspectionDetailView.as_view(), name='inspection_detail'),
    path('inspections/<int:pk>/edit/', views.SafetyInspectionUpdateView.as_view(), name='inspection_update'),
    path('incidents/', views.IncidentReportListView.as_view(), name='incident_list'),
    path('incidents/create/', views.IncidentReportCreateView.as_view(), name='incident_create'),
    path('incidents/<int:pk>/', views.IncidentReportDetailView.as_view(), name='incident_detail'),
    path('incidents/<int:pk>/edit/', views.IncidentReportUpdateView.as_view(), name='incident_update'),
    path('jsea/', views.JSEARecordListView.as_view(), name='jsea_list'),
    path('jsea/create/', views.JSEARecordCreateView.as_view(), name='jsea_create'),
    path('toolbox/<int:pk>/delete/', views.ToolboxMeetingDeleteView.as_view(), name='toolbox_delete'),
    path('inspections/<int:pk>/delete/', views.SafetyInspectionDeleteView.as_view(), name='inspection_delete'),
    path('incidents/<int:pk>/delete/', views.IncidentReportDeleteView.as_view(), name='incident_delete'),
    path('jsea/<int:pk>/delete/', views.JSEARecordDeleteView.as_view(), name='jsea_delete'),
]
