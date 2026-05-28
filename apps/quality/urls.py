from django.urls import path

from . import views

app_name = 'quality'

urlpatterns = [
    path('', views.QualityDashboardView.as_view(), name='dashboard'),
    path('inspections/', views.InspectionRequestListView.as_view(), name='inspection_list'),
    path('inspections/create/', views.InspectionRequestCreateView.as_view(), name='inspection_create'),
    path('inspections/<int:pk>/edit/', views.InspectionRequestUpdateView.as_view(), name='inspection_update'),
    path('inspections/<int:pk>/delete/', views.InspectionRequestDeleteView.as_view(), name='inspection_delete'),
    path('ncr/', views.NonConformanceListView.as_view(), name='ncr_list'),
    path('ncr/create/', views.NonConformanceCreateView.as_view(), name='ncr_create'),
    path('ncr/<int:pk>/edit/', views.NonConformanceUpdateView.as_view(), name='ncr_update'),
    path('ncr/<int:pk>/delete/', views.NonConformanceDeleteView.as_view(), name='ncr_delete'),
    path('punch-list/', views.PunchListView.as_view(), name='punch_list'),
    path('punch-list/create/', views.PunchListCreateView.as_view(), name='punch_create'),
    path('punch-list/<int:pk>/edit/', views.PunchListUpdateView.as_view(), name='punch_update'),
    path('punch-list/<int:pk>/delete/', views.PunchListDeleteView.as_view(), name='punch_delete'),
    path('checkpoints/', views.QualityCheckpointListView.as_view(), name='checkpoint_list'),
    path('checkpoints/create/', views.QualityCheckpointCreateView.as_view(), name='checkpoint_create'),
    path('checkpoints/<int:pk>/edit/', views.QualityCheckpointUpdateView.as_view(), name='checkpoint_update'),
    path('checkpoints/<int:pk>/delete/', views.QualityCheckpointDeleteView.as_view(), name='checkpoint_delete'),
]
