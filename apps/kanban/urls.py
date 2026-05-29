from django.urls import path
from . import views

app_name = 'kanban'

urlpatterns = [
    path('', views.KanbanBoardView.as_view(), name='board'),
    path('tasks/create/', views.KanbanTaskCreateView.as_view(), name='task_create'),
    path('tasks/<int:pk>/edit/', views.KanbanTaskUpdateView.as_view(), name='task_edit'),
    path('tasks/<int:pk>/delete/', views.KanbanTaskDeleteView.as_view(), name='task_delete'),
    path('tasks/<int:pk>/move/', views.KanbanTaskMoveView.as_view(), name='task_move'),
]
