from rest_framework import serializers
from .models import EquipmentCategory, Equipment, DailyEquipmentRecord


class EquipmentCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentCategory
        fields = '__all__'


class EquipmentSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Equipment
        fields = '__all__'


class DailyEquipmentRecordSerializer(serializers.ModelSerializer):
    equipment_name = serializers.CharField(source='equipment.name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = DailyEquipmentRecord
        fields = '__all__'
