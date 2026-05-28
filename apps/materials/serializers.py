from rest_framework import serializers
from .models import MaterialCategory, Material, MaterialDelivery, MaterialUsage


class MaterialCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialCategory
        fields = '__all__'


class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Material
        fields = '__all__'


class MaterialDeliverySerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = MaterialDelivery
        fields = '__all__'


class MaterialUsageSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)

    class Meta:
        model = MaterialUsage
        fields = '__all__'
