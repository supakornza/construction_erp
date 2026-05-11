from django.urls import path
from . import views

app_name = 'equipment'

urlpatterns = [
    path('', views.EquipmentListView.as_view(), name='list'),
    path('create/', views.EquipmentCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='delete'),
    path('records/', views.DailyEquipmentRecordListView.as_view(), name='record_list'),
    path('records/create/', views.DailyEquipmentRecordCreateView.as_view(), name='record_create'),
    path('records/<int:pk>/edit/', views.DailyEquipmentRecordUpdateView.as_view(), name='record_update'),
    path('records/<int:pk>/delete/', views.DailyEquipmentRecordDeleteView.as_view(), name='record_delete'),
]
