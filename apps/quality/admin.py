from django.contrib import admin

from .models import InspectionRequest, NonConformance, PunchList, QualityCheckpoint


@admin.register(InspectionRequest)
class InspectionRequestAdmin(admin.ModelAdmin):
    list_display = [
        'inspection_date', 'project', 'inspection_type', 'location',
        'status', 'result', 'requested_by', 'inspected_by',
    ]
    list_filter = ['status', 'result', 'inspection_type', 'project', 'inspection_date']
    search_fields = [
        'inspection_type', 'description', 'location', 'station_or_chainage',
        'project__project_name', 'project__contract_no', 'boq_item__item_no',
    ]
    date_hierarchy = 'inspection_date'
    autocomplete_fields = ['project', 'boq_item', 'requested_by', 'inspected_by']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(QualityCheckpoint)
class QualityCheckpointAdmin(admin.ModelAdmin):
    list_display = ['checkpoint_name', 'project', 'boq_item', 'specification_ref', 'frequency', 'is_active']
    list_filter = ['is_active', 'project']
    search_fields = [
        'checkpoint_name', 'specification_ref', 'acceptance_criteria',
        'project__project_name', 'project__contract_no', 'boq_item__item_no',
    ]
    autocomplete_fields = ['project', 'boq_item']


@admin.register(NonConformance)
class NonConformanceAdmin(admin.ModelAdmin):
    list_display = ['ncr_no', 'project', 'severity', 'status', 'issued_date', 'due_date', 'closed_date', 'responsible_person', 'attachment']
    list_filter = ['status', 'severity', 'project', 'issued_date', 'due_date']
    search_fields = [
        'ncr_no', 'description', 'root_cause', 'corrective_action',
        'project__project_name', 'project__contract_no', 'boq_item__item_no',
    ]
    date_hierarchy = 'issued_date'
    autocomplete_fields = ['project', 'inspection_request', 'boq_item', 'responsible_person']


@admin.register(PunchList)
class PunchListAdmin(admin.ModelAdmin):
    list_display = ['project', 'priority', 'status', 'location', 'target_date', 'closed_date', 'responsible_person', 'attachment']
    list_filter = ['status', 'priority', 'project', 'target_date']
    search_fields = ['description', 'location', 'project__project_name', 'project__contract_no']
    date_hierarchy = 'target_date'
    autocomplete_fields = ['project', 'responsible_person']
