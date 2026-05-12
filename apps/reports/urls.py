from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('daily-report/<int:pk>/pdf/', views.DailyReportPDFView.as_view(), name='daily_report_pdf'),
    path('daily-report/<int:pk>/pmc-pdf/', views.PMCDailyReportPDFView.as_view(), name='pmc_daily_report_pdf'),
    path('daily-report/<int:pk>/pmc-excel/', views.PMCDailyReportExcelView.as_view(), name='pmc_daily_report_excel'),
    path('project/<int:project_pk>/materials/excel/', views.MaterialDeliveryExcelView.as_view(), name='material_delivery_excel'),
    path('project/<int:project_pk>/boq/excel/', views.BOQProgressExcelView.as_view(), name='boq_progress_excel'),
    path('project/<int:project_pk>/safety/excel/', views.SafetyObservationExcelView.as_view(), name='safety_excel'),
]
