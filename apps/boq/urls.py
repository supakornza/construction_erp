from django.urls import path
from . import views

app_name = 'boq'

urlpatterns = [
    path('', views.BOQItemListView.as_view(), name='list'),
    path('create/', views.BOQItemCreateView.as_view(), name='create'),
    path('import/', views.BOQImportView.as_view(), name='import'),
    path('<int:pk>/edit/', views.BOQItemUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.BOQItemDeleteView.as_view(), name='delete'),
    path('progress/', views.DailyProgressRecordListView.as_view(), name='progress_list'),
    path('progress/create/', views.DailyProgressRecordCreateView.as_view(), name='progress_create'),
    path('claims/', views.PaymentClaimListView.as_view(), name='claim_list'),
    path('claims/create/', views.PaymentClaimCreateView.as_view(), name='claim_create'),
    path('claims/<int:pk>/', views.PaymentClaimDetailView.as_view(), name='claim_detail'),
]
