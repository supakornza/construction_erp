from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('dashboard/', views.MaterialDeliveryDashboardView.as_view(), name='dashboard'),
    path('', views.MaterialListView.as_view(), name='list'),
    path('create/', views.MaterialCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.MaterialUpdateView.as_view(), name='update'),
    path('deliveries/', views.MaterialDeliveryListView.as_view(), name='delivery_list'),
    path('deliveries/export/excel/', views.MaterialDeliveryExportExcelView.as_view(), name='delivery_export_excel'),
    path('deliveries/export/pdf/', views.MaterialDeliveryExportPDFView.as_view(), name='delivery_export_pdf'),
    path('deliveries/create/', views.MaterialDeliveryCreateView.as_view(), name='delivery_create'),
    path('deliveries/ocr-preview/', views.ocr_preview, name='delivery_ocr_preview'),
    path('deliveries/<int:pk>/edit/', views.MaterialDeliveryUpdateView.as_view(), name='delivery_update'),
    path('deliveries/<int:pk>/delete/', views.MaterialDeliveryDeleteView.as_view(), name='delivery_delete'),
    path('usage/', views.MaterialUsageListView.as_view(), name='usage_list'),
    path('usage/create/', views.MaterialUsageCreateView.as_view(), name='usage_create'),
    path('stock/', views.StockBalanceView.as_view(), name='stock'),
]
