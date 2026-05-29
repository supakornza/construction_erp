from django.contrib import admin
from .models import KanbanTask


@admin.register(KanbanTask)
class KanbanTaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'column', 'priority', 'project', 'assignee', 'due_date', 'created_at']
    list_filter = ['column', 'priority', 'project']
    search_fields = ['title', 'description']
    ordering = ['column', 'order']
