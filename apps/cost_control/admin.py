from django.contrib import admin
from .models import CostCode, BudgetItem, ActualCost


@admin.register(CostCode)
class CostCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'project', 'is_active', 'created_at')
    list_filter = ('project', 'is_active')
    search_fields = ('code', 'name', 'description')
    list_per_page = 50


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('cost_code', 'description', 'project', 'budget_amount', 'committed_amount')
    list_filter = ('project', 'cost_code')
    search_fields = ('description', 'cost_code__code', 'remarks')
    raw_id_fields = ('boq_item',)
    list_per_page = 50


@admin.register(ActualCost)
class ActualCostAdmin(admin.ModelAdmin):
    list_display = ('description', 'project', 'cost_code', 'cost_date', 'source_type', 'amount', 'reference_no')
    list_filter = ('project', 'cost_code', 'source_type', 'cost_date')
    search_fields = ('description', 'reference_no', 'cost_code__code', 'remarks')
    date_hierarchy = 'cost_date'
    list_per_page = 50
