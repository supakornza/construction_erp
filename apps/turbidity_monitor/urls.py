from django.urls import path
from . import views

app_name = 'turbidity_monitor'

urlpatterns = [
    path('', views.TurbidityMonitorView.as_view(), name='dashboard'),
    path('api/data/', views.TurbidityDataAPIView.as_view(), name='api_data'),
]
