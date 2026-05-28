from django.contrib import admin
from .models import EquipmentCategory, Equipment, EquipmentPhoto, DailyEquipmentRecord


@admin.register(EquipmentCategory)
class EquipmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


class EquipmentPhotoInline(admin.TabularInline):
    model = EquipmentPhoto
    extra = 1
    fields = ['image', 'caption', 'uploaded_at']
    readonly_fields = ['uploaded_at']


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'registration_no', 'project', 'status', 'photo_count']
    list_filter = ['category', 'status', 'project']
    search_fields = ['name', 'registration_no']
    inlines = [EquipmentPhotoInline]

    @admin.display(description='Photos')
    def photo_count(self, obj):
        return obj.photos.count()


@admin.register(DailyEquipmentRecord)
class DailyEquipmentRecordAdmin(admin.ModelAdmin):
    list_display = ['report_date', 'project', 'equipment', 'status', 'working_hours']
    list_filter = ['status', 'project']
    search_fields = ['equipment__name']
    date_hierarchy = 'report_date'
