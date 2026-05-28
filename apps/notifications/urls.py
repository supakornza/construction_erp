from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('',                        views.NotificationListView.as_view(),      name='list'),
    path('<int:pk>/read/',          views.NotificationMarkReadView.as_view(),   name='mark_read'),
    path('read-all/',               views.NotificationMarkAllReadView.as_view(), name='mark_all_read'),
    path('<int:pk>/delete/',        views.NotificationDeleteView.as_view(),     name='delete'),
    path('delete-read/',            views.NotificationDeleteAllView.as_view(),  name='delete_read'),
]
