from django.urls import path
from . import views

app_name = 'cost_control'

urlpatterns = [
    path('', views.CostDashboardView.as_view(), name='dashboard'),

    # Cost Codes
    path('codes/', views.CostCodeListView.as_view(), name='cost_code_list'),
    path('codes/new/', views.CostCodeCreateView.as_view(), name='cost_code_create'),
    path('codes/<int:pk>/edit/', views.CostCodeUpdateView.as_view(), name='cost_code_update'),
    path('codes/<int:pk>/delete/', views.CostCodeDeleteView.as_view(), name='cost_code_delete'),

    # Budget Items
    path('budget/', views.BudgetItemListView.as_view(), name='budget_list'),
    path('budget/new/', views.BudgetItemCreateView.as_view(), name='budget_create'),
    path('budget/<int:pk>/edit/', views.BudgetItemUpdateView.as_view(), name='budget_update'),
    path('budget/<int:pk>/delete/', views.BudgetItemDeleteView.as_view(), name='budget_delete'),

    # Actual Costs
    path('actuals/', views.ActualCostListView.as_view(), name='actual_cost_list'),
    path('actuals/new/', views.ActualCostCreateView.as_view(), name='actual_cost_create'),
    path('actuals/<int:pk>/edit/', views.ActualCostUpdateView.as_view(), name='actual_cost_update'),
    path('actuals/<int:pk>/delete/', views.ActualCostDeleteView.as_view(), name='actual_cost_delete'),
]
