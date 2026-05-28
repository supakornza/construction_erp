from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('create/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='delete'),
    path('<int:project_pk>/stakeholders/add/', views.StakeholderCreateView.as_view(), name='stakeholder_add'),
    path('<int:project_pk>/work-areas/add/', views.WorkAreaCreateView.as_view(), name='work_area_add'),
    path('work-areas/<int:pk>/edit/', views.WorkAreaUpdateView.as_view(), name='work_area_update'),
]
