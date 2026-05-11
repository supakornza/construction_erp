from django.urls import path
from . import views

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
]
