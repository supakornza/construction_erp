from django.contrib import admin
from .models import ChangeOrder, ChangeOrderItem


class ChangeOrderItemInline(admin.TabularInline):
    model  = ChangeOrderItem
    extra  = 0
    fields = ['change_type', 'boq_item', 'description', 'unit',
              'original_quantity', 'revised_quantity', 'unit_rate', 'remarks']


@admin.register(ChangeOrder)
class ChangeOrderAdmin(admin.ModelAdmin):
    list_display  = ['co_no', 'project', 'title', 'type', 'status',
                     'contract_value_impact', 'time_impact_days', 'initiated_date']
    list_filter   = ['status', 'type', 'project']
    search_fields = ['co_no', 'title', 'description']
    inlines       = [ChangeOrderItemInline]
    readonly_fields = ['created_at', 'updated_at']
