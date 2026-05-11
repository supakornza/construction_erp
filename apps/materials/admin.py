from django.contrib import admin
from .models import MaterialCategory, Material, MaterialDelivery, MaterialUsage


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'unit', 'unit_weight']
    list_filter = ['category']
    search_fields = ['name']


@admin.register(MaterialDelivery)
class MaterialDeliveryAdmin(admin.ModelAdmin):
    list_display = ['delivery_date', 'project', 'material', 'quantity', 'delivery_note_no']
    list_filter = ['project', 'material']
    search_fields = ['delivery_note_no', 'truck_no']
    date_hierarchy = 'delivery_date'


@admin.register(MaterialUsage)
class MaterialUsageAdmin(admin.ModelAdmin):
    list_display = ['usage_date', 'project', 'material', 'quantity', 'work_area']
    list_filter = ['project', 'material']
    date_hierarchy = 'usage_date'
