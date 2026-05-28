from django.contrib import admin
from .models import Project, Stakeholder, WorkArea


class StakeholderInline(admin.TabularInline):
    model = Stakeholder
    extra = 1


class WorkAreaInline(admin.TabularInline):
    model = WorkArea
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['contract_no', 'project_name', 'status', 'start_date', 'finish_date', 'contract_value', 'created_by']
    list_filter = ['status']
    search_fields = ['project_name', 'contract_no', 'owner', 'contractor']
    date_hierarchy = 'start_date'
    inlines = [StakeholderInline, WorkAreaInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Stakeholder)
class StakeholderAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'role', 'project', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['name', 'company', 'email']


@admin.register(WorkArea)
class WorkAreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'area_sqm']
    search_fields = ['name', 'project__project_name']
    list_filter = ['project']
