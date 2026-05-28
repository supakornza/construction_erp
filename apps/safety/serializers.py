from rest_framework import serializers
from .models import ToolboxMeeting, SafetyInspection, IncidentReport, JSEARecord


class ToolboxMeetingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ToolboxMeeting
        fields = '__all__'


class SafetyInspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyInspection
        fields = '__all__'


class IncidentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = '__all__'


class JSEARecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = JSEARecord
        fields = '__all__'
