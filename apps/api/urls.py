from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet)
router.register(r'daily-reports', views.DailyReportViewSet)
router.register(r'manpower/records', views.ManpowerRecordViewSet)
router.register(r'equipment/records', views.EquipmentRecordViewSet)
router.register(r'materials/deliveries', views.MaterialDeliveryViewSet)
router.register(r'materials/stock', views.MaterialStockViewSet, basename='material-stock')
router.register(r'boq/items', views.BOQItemViewSet)
router.register(r'boq/progress', views.BOQProgressViewSet)
router.register(r'safety/inspections', views.SafetyInspectionViewSet)
router.register(r'documents', views.DocumentViewSet)
router.register(r'dashboard/chart-data', views.DashboardChartDataViewSet, basename='dashboard-chart')
router.register(r'materials/transport-summary', views.MaterialTransportSummaryViewSet, basename='material-transport-summary')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
