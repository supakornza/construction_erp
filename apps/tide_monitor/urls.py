from django.urls import path
from . import views

app_name = 'tide_monitor'

urlpatterns = [
    path('', views.TideMonitorView.as_view(), name='dashboard'),
    path('api/data/', views.TideDataAPIView.as_view(), name='api_data'),
]
