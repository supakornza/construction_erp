from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='index'),
    path('chart-data/', views.DashboardChartDataView.as_view(), name='chart_data'),
    path('scurve/', views.SCurveDataView.as_view(), name='scurve_data'),
]
