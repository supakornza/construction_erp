from django.contrib import admin
from .models import BOQItem, DailyProgressRecord, PaymentClaim


class DailyProgressRecordInline(admin.TabularInline):
    model = DailyProgressRecord
    extra = 1


@admin.register(BOQItem)
class BOQItemAdmin(admin.ModelAdmin):
    list_display = ['item_no', 'category', 'description', 'project', 'unit', 'contract_quantity', 'unit_rate']
    list_filter = ['project', 'category']
    search_fields = ['item_no', 'description']
    inlines = [DailyProgressRecordInline]


@admin.register(DailyProgressRecord)
class DailyProgressRecordAdmin(admin.ModelAdmin):
    list_display = ['record_date', 'project', 'boq_item', 'daily_quantity']
    list_filter = ['project']
    search_fields = ['boq_item__description']
    date_hierarchy = 'record_date'


@admin.register(PaymentClaim)
class PaymentClaimAdmin(admin.ModelAdmin):
    list_display = ['claim_no', 'project', 'claim_date', 'total_claimed_amount', 'status']
    list_filter = ['status', 'project']
    date_hierarchy = 'claim_date'
