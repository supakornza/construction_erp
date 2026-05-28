from rest_framework import serializers
from .models import DailyReport, DailyWorkActivity, DailyLookahead, DailyProblemRemark, DailyPhoto


class DailyWorkActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyWorkActivity
        fields = '__all__'


class DailyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPhoto
        fields = '__all__'


class DailyReportSerializer(serializers.ModelSerializer):
    activities = DailyWorkActivitySerializer(many=True, read_only=True)
    photos = DailyPhotoSerializer(many=True, read_only=True)
    prepared_by_name = serializers.CharField(source='prepared_by.get_full_name', read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = DailyReport
        fields = '__all__'
