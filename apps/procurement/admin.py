from django.contrib import admin
from .models import Supplier, PurchaseRequest, PurchaseRequestItem, PurchaseOrder, PurchaseOrderItem


class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 1


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email']
    search_fields = ['name', 'contact_person', 'tax_id']


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ['pr_no', 'project', 'requested_by', 'request_date', 'status']
    list_filter = ['status', 'project']
    search_fields = ['pr_no']
    date_hierarchy = 'request_date'
    inlines = [PurchaseRequestItemInline]


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_no', 'pr', 'supplier', 'order_date', 'status', 'total_amount']
    list_filter = ['status', 'supplier']
    search_fields = ['po_no']
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderItemInline]
