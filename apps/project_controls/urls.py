from django.urls import path
from . import views

app_name = 'project_controls'

urlpatterns = [
    # Main dashboard
    path('', views.ProjectControlsDashboardView.as_view(), name='dashboard'),

    # Rock
    path('rock/', views.RockListView.as_view(), name='rock_list'),
    path('rock/new/', views.RockCreateView.as_view(), name='rock_create'),
    path('rock/<int:pk>/', views.RockDetailView.as_view(), name='rock_detail'),
    path('rock/<int:pk>/edit/', views.RockUpdateView.as_view(), name='rock_update'),
    path('rock/<int:pk>/delete/', views.RockDeleteView.as_view(), name='rock_delete'),
    path('rock/dashboard/', views.RockDashboardView.as_view(), name='rock_dashboard'),
    path('rock/export/<int:project_id>/', views.RockExportExcelView.as_view(), name='rock_export_excel'),
    path('rock/<int:pk>/pdf/', views.RockExportPDFView.as_view(), name='rock_export_pdf'),
    path('rock/chart-data/', views.RockChartDataView.as_view(), name='rock_chart_data'),

    # Sand
    path('sand/', views.SandListView.as_view(), name='sand_list'),
    path('sand/new/', views.SandCreateView.as_view(), name='sand_create'),
    path('sand/<int:pk>/', views.SandDetailView.as_view(), name='sand_detail'),
    path('sand/<int:pk>/edit/', views.SandUpdateView.as_view(), name='sand_update'),
    path('sand/<int:pk>/delete/', views.SandDeleteView.as_view(), name='sand_delete'),
    path('sand/dashboard/', views.SandDashboardView.as_view(), name='sand_dashboard'),
    path('sand/export/<int:project_id>/', views.SandExportExcelView.as_view(), name='sand_export_excel'),
    path('sand/chart-data/', views.SandChartDataView.as_view(), name='sand_chart_data'),

    # Sand Allocation
    path('sand/allocation/', views.SandAllocationListView.as_view(), name='sand_allocation_list'),
    path('sand/allocation/new/', views.SandAllocationCreateView.as_view(), name='sand_allocation_create'),
    path('sand/allocation/<int:pk>/', views.SandAllocationDetailView.as_view(), name='sand_allocation_detail'),

    # Revetment Progress
    path('revetment/', views.RevetmentRecordListView.as_view(), name='revetment_list'),
    path('revetment/new/', views.RevetmentRecordCreateView.as_view(), name='revetment_create'),
    path('revetment/<int:pk>/', views.RevetmentRecordDetailView.as_view(), name='revetment_detail'),
    path('revetment/<int:pk>/edit/', views.RevetmentRecordUpdateView.as_view(), name='revetment_update'),
    path('revetment/dashboard/', views.RevetmentDashboardView.as_view(), name='revetment_dashboard'),
    path('revetment/setup/', views.RevetmentSetupView.as_view(), name='revetment_setup'),
    path('revetment/setup/stations/new/', views.RevetmentStationCreateView.as_view(), name='revetment_station_create'),
    path('revetment/setup/stations/<int:pk>/edit/', views.RevetmentStationUpdateView.as_view(), name='revetment_station_update'),
    path('revetment/setup/activities/new/', views.RevetmentActivityCreateView.as_view(), name='revetment_activity_create'),
    path('revetment/setup/activities/<int:pk>/edit/', views.RevetmentActivityUpdateView.as_view(), name='revetment_activity_update'),
    path('revetment/export/<int:project_id>/', views.RevetmentExportExcelView.as_view(), name='revetment_export_excel'),

    # 14-Day Recovery Plan
    path('recovery/plans/', views.RecoveryPlanListView.as_view(), name='recovery_plan_list'),
    path('recovery/plans/new/', views.RecoveryPlanCreateView.as_view(), name='recovery_plan_create'),
    path('recovery/plans/<int:pk>/', views.RecoveryPlanDetailView.as_view(), name='recovery_plan_detail'),
    path('recovery/plans/<int:pk>/edit/', views.RecoveryPlanUpdateView.as_view(), name='recovery_plan_update'),
    path('recovery/plans/<int:pk>/daily/', views.RecoveryPlanDailyUpdateView.as_view(), name='recovery_plan_daily'),

    # Recovery Action Plan
    path('recovery/rap/', views.RecoveryActionPlanListView.as_view(), name='rap_list'),
    path('recovery/rap/new/', views.RecoveryActionPlanCreateView.as_view(), name='rap_create'),
    path('recovery/rap/<int:pk>/', views.RecoveryActionPlanDetailView.as_view(), name='rap_detail'),
    path('recovery/rap/<int:pk>/edit/', views.RecoveryActionPlanUpdateView.as_view(), name='rap_update'),
    path('recovery/rap/<int:pk>/submit/', views.RAPSubmitView.as_view(), name='rap_submit'),
    path('recovery/rap/<int:pk>/approve/', views.RAPApproveView.as_view(), name='rap_approve'),
    path('recovery/rap/<int:pk>/reject/', views.RAPRejectView.as_view(), name='rap_reject'),
    path('recovery/rap/<int:pk>/export/', views.RAPExportExcelView.as_view(), name='rap_export_excel'),
    path('recovery/rap/<int:pk>/pdf/', views.RAPExportPDFView.as_view(), name='rap_export_pdf'),
    path('recovery/rap/dashboard/', views.RecoveryDashboardView.as_view(), name='recovery_dashboard'),

    # Progress entry
    path('recovery/item/<int:item_pk>/progress/new/',
         views.RecoveryActionDailyProgressCreateView.as_view(), name='progress_create'),

    # Project Management Action Plan
    path('action-plans/', views.ProjectActionPlanListView.as_view(), name='project_action_plan_list'),
    path('action-plans/new/', views.ProjectActionPlanCreateView.as_view(), name='project_action_plan_create'),
    path('action-plans/<int:pk>/', views.ProjectActionPlanDetailView.as_view(), name='project_action_plan_detail'),
    path('action-plans/<int:pk>/edit/', views.ProjectActionPlanUpdateView.as_view(), name='project_action_plan_update'),
    path('action-plans/<int:pk>/delete/', views.ProjectActionPlanDeleteView.as_view(), name='project_action_plan_delete'),

    # Logistics
    path('logistics/', views.LogisticsScenarioListView.as_view(), name='logistics_list'),
    path('logistics/new/', views.LogisticsScenarioCreateView.as_view(), name='logistics_create'),
    path('logistics/<int:pk>/', views.LogisticsScenarioDetailView.as_view(), name='logistics_detail'),
    path('logistics/<int:pk>/edit/', views.LogisticsScenarioUpdateView.as_view(), name='logistics_update'),
    path('logistics/<int:pk>/delete/', views.LogisticsScenarioDeleteView.as_view(), name='logistics_delete'),
    path('logistics/compare/', views.LogisticsComparisonView.as_view(), name='logistics_compare'),

    # Import
    path('import/', views.ImportView.as_view(), name='import'),
    path('import/logs/', views.ImportLogListView.as_view(), name='import_log_list'),
    path('import/logs/<int:pk>/', views.ImportLogDetailView.as_view(), name='import_log_detail'),
]
