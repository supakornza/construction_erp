from rest_framework import serializers
from .models import ManpowerCategory, DailyManpowerRecord


class ManpowerCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ManpowerCategory
        fields = '__all__'


class DailyManpowerRecordSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.get_name_display', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = DailyManpowerRecord
        fields = '__all__'
