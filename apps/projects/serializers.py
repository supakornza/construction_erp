from rest_framework import serializers
from .models import Project, Stakeholder, WorkArea


class StakeholderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stakeholder
        fields = '__all__'


class WorkAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkArea
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    stakeholders = StakeholderSerializer(many=True, read_only=True)
    work_areas = WorkAreaSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Project
        fields = '__all__'
