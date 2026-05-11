from django.urls import path
from . import views

app_name = 'manpower'

urlpatterns = [
    path('', views.DailyManpowerRecordListView.as_view(), name='list'),
    path('create/', views.DailyManpowerRecordCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.DailyManpowerRecordUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.DailyManpowerRecordDeleteView.as_view(), name='delete'),
    path('histogram/', views.ManpowerHistogramView.as_view(), name='histogram'),
]
