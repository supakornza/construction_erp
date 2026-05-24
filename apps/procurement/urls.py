from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    path('', views.ProcurementIndexView.as_view(), name='index'),
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/create/', views.SupplierCreateView.as_view(), name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_update'),
    path('pr/', views.PurchaseRequestListView.as_view(), name='pr_list'),
    path('pr/create/', views.PurchaseRequestCreateView.as_view(), name='pr_create'),
    path('pr/<int:pk>/', views.PurchaseRequestDetailView.as_view(), name='pr_detail'),
    path('po/', views.PurchaseOrderListView.as_view(), name='po_list'),
    path('po/create/', views.PurchaseOrderCreateView.as_view(), name='po_create'),
    path('po/<int:pk>/', views.PurchaseOrderDetailView.as_view(), name='po_detail'),
]
