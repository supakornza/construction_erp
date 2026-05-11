from rest_framework import serializers
from .models import DocumentCategory, Document, DocumentRevision


class DocumentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentCategory
        fields = '__all__'


class DocumentRevisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentRevision
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    revisions = DocumentRevisionSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
