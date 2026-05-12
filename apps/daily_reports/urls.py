from django.urls import path
from . import views, import_views

app_name = 'daily_reports'

urlpatterns = [
    path('', views.DailyReportListView.as_view(), name='list'),
    path('create/', views.DailyReportCreateView.as_view(), name='create'),
    path('<int:pk>/', views.DailyReportDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.DailyReportUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.DailyReportDeleteView.as_view(), name='delete'),
    path('<int:pk>/submit/', views.SubmitReportView.as_view(), name='submit'),
    path('<int:pk>/approve/', views.ApproveReportView.as_view(), name='approve'),
    path('<int:pk>/reject/', views.RejectReportView.as_view(), name='reject'),
    path('<int:pk>/pdf/', views.ExportPDFView.as_view(), name='export_pdf'),

    # Contractor import workflow
    path('import/', import_views.ImportListView.as_view(), name='import_list'),
    path('import/upload/', import_views.ImportUploadView.as_view(), name='import_upload'),
    path('import/preview/', import_views.ImportPreviewView.as_view(), name='import_preview'),
    path('import/pdf-edit/', import_views.ImportPdfEditView.as_view(), name='import_pdf_edit'),
    path('import/template/', import_views.ImportTemplateDownloadView.as_view(), name='import_template'),
    path('import/<int:pk>/', import_views.ImportDetailView.as_view(), name='import_detail'),
    path('import/<int:pk>/create-report/', import_views.ImportCreateReportView.as_view(), name='import_create_report'),
    path('import/<int:pk>/delete/', import_views.ImportDeleteView.as_view(), name='import_delete'),
]
