from django.contrib import admin
from .models import Subcontractor, SubcontractorContract, SubcontractorWorkItem, PaymentClaim


class WorkItemInline(admin.TabularInline):
    model = SubcontractorWorkItem
    extra = 0


class PaymentClaimInline(admin.TabularInline):
    model  = PaymentClaim
    extra  = 0
    fields = ['claim_no', 'claim_date', 'claimed_amount', 'certified_amount', 'net_payable', 'status']
    readonly_fields = ['claim_no']


@admin.register(Subcontractor)
class SubcontractorAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'status', 'contact_person', 'phone', 'email']
    list_filter   = ['category', 'status']
    search_fields = ['name', 'registration_no', 'tax_id']


@admin.register(SubcontractorContract)
class SubcontractorContractAdmin(admin.ModelAdmin):
    list_display  = ['contract_no', 'title', 'project', 'subcontractor', 'contract_type',
                     'contract_value', 'status']
    list_filter   = ['status', 'contract_type']
    search_fields = ['contract_no', 'title', 'subcontractor__name']
    inlines       = [WorkItemInline, PaymentClaimInline]
    readonly_fields = ['contract_no']


@admin.register(PaymentClaim)
class PaymentClaimAdmin(admin.ModelAdmin):
    list_display  = ['claim_no', 'contract', 'claim_date', 'claimed_amount',
                     'certified_amount', 'net_payable', 'status']
    list_filter   = ['status']
    search_fields = ['claim_no', 'contract__contract_no', 'contract__subcontractor__name']
    readonly_fields = ['claim_no']
