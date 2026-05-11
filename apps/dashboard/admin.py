from django.contrib import admin
from .models import OwnerDecisionItem


@admin.register(OwnerDecisionItem)
class OwnerDecisionItemAdmin(admin.ModelAdmin):
    list_display = ('project', 'issue', 'priority', 'status', 'due_date', 'responsible_party')
    list_filter = ('priority', 'status', 'project')
    search_fields = ('issue', 'impact', 'responsible_party')
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('project', 'priority', 'status')}),
        ('Issue Details', {'fields': ('issue', 'impact', 'decision_required')}),
        ('Assignment', {'fields': ('responsible_party', 'due_date')}),
        ('Meta', {'fields': ('created_by', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
