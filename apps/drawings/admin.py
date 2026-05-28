from django.contrib import admin
from .models import Drawing, RFI


@admin.register(Drawing)
class DrawingAdmin(admin.ModelAdmin):
    list_display  = ['drawing_no', 'revision', 'title', 'discipline', 'status',
                     'issue_date', 'project']
    list_filter   = ['discipline', 'status', 'project']
    search_fields = ['drawing_no', 'title']
    readonly_fields = ['created_at']


@admin.register(RFI)
class RFIAdmin(admin.ModelAdmin):
    list_display  = ['rfi_no', 'subject', 'project', 'priority', 'status',
                     'response_required_date', 'answered_by']
    list_filter   = ['status', 'priority', 'project']
    search_fields = ['rfi_no', 'subject']
    readonly_fields = ['rfi_no', 'created_at']
