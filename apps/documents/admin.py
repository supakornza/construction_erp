from django.contrib import admin
from .models import DocumentCategory, Document, DocumentRevision


class DocumentRevisionInline(admin.TabularInline):
    model = DocumentRevision
    extra = 1


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['document_no', 'title', 'project', 'category', 'revision', 'status', 'uploaded_by', 'uploaded_at']
    list_filter = ['status', 'category', 'project']
    search_fields = ['document_no', 'title']
    date_hierarchy = 'uploaded_at'
    inlines = [DocumentRevisionInline]
