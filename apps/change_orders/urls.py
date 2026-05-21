from django.urls import path
from . import views

app_name = 'change_orders'

urlpatterns = [
    path('',                        views.ChangeOrderListView.as_view(),   name='list'),
    path('create/',                 views.ChangeOrderCreateView.as_view(), name='create'),
    path('<int:pk>/',               views.ChangeOrderDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/',          views.ChangeOrderUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/',        views.ChangeOrderDeleteView.as_view(), name='delete'),
    path('<int:pk>/submit/',        views.ChangeOrderSubmitView.as_view(), name='submit'),
    path('<int:pk>/review/',        views.ChangeOrderReviewView.as_view(), name='review'),
    path('<int:pk>/approve/',       views.ChangeOrderApproveView.as_view(), name='approve'),
    path('<int:pk>/reject/',        views.ChangeOrderRejectView.as_view(), name='reject'),
    path('<int:pk>/cancel/',        views.ChangeOrderCancelView.as_view(), name='cancel'),
]
