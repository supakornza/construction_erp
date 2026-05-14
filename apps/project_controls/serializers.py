from rest_framework import serializers
from .models import (
    Barge, RockDailyRecord, RockBargePlacement,
    SandDailyRecord, SandBargePlacement, SandAllocation,
    RecoveryPlan, RecoveryPlanDailyItem,
    RecoveryActionPlan, RecoveryActionItem, RecoveryActionDailyProgress,
    LogisticsScenario,
)


class BargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Barge
        fields = '__all__'


class RockBargePlacementSerializer(serializers.ModelSerializer):
    barge_name = serializers.CharField(source='barge.name', read_only=True)

    class Meta:
        model = RockBargePlacement
        fields = ['id', 'barge', 'barge_name', 'quantity_ton', 'trips', 'placement_type', 'station', 'remarks']


class RockDailyRecordSerializer(serializers.ModelSerializer):
    barge_placements = RockBargePlacementSerializer(many=True, read_only=True)
    stock_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = RockDailyRecord
        fields = '__all__'


class SandBargePlacementSerializer(serializers.ModelSerializer):
    barge_name = serializers.CharField(source='barge.name', read_only=True)

    class Meta:
        model = SandBargePlacement
        fields = ['id', 'barge', 'barge_name', 'quantity_ton', 'trips', 'source',
                  'destination', 'placement_type', 'material_type', 'status', 'station']


class SandDailyRecordSerializer(serializers.ModelSerializer):
    barge_placements = SandBargePlacementSerializer(many=True, read_only=True)
    total_remaining = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = SandDailyRecord
        fields = '__all__'


class SandAllocationSerializer(serializers.ModelSerializer):
    calculated_tct_quantity = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    calculated_mtp3_quantity = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    calculated_tct_trips = serializers.IntegerField(read_only=True)
    calculated_mtp3_trips = serializers.IntegerField(read_only=True)

    class Meta:
        model = SandAllocation
        fields = '__all__'


class RecoveryPlanDailyItemSerializer(serializers.ModelSerializer):
    deviation = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    achievement_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = RecoveryPlanDailyItem
        fields = '__all__'


class RecoveryPlanSerializer(serializers.ModelSerializer):
    daily_items = RecoveryPlanDailyItemSerializer(many=True, read_only=True)
    total_planned = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_actual = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    achievement_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = RecoveryPlan
        fields = '__all__'


class RecoveryActionDailyProgressSerializer(serializers.ModelSerializer):
    deviation = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    percent_complete = serializers.FloatField(read_only=True)

    class Meta:
        model = RecoveryActionDailyProgress
        fields = '__all__'


class RecoveryActionItemSerializer(serializers.ModelSerializer):
    daily_progress = RecoveryActionDailyProgressSerializer(many=True, read_only=True)
    total_planned = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    total_actual = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    percent_complete = serializers.FloatField(read_only=True)
    latest_status = serializers.CharField(read_only=True)

    class Meta:
        model = RecoveryActionItem
        fields = '__all__'


class RecoveryActionPlanSerializer(serializers.ModelSerializer):
    items = RecoveryActionItemSerializer(many=True, read_only=True)
    overall_percent_complete = serializers.FloatField(read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = RecoveryActionPlan
        fields = '__all__'


class LogisticsScenarioSerializer(serializers.ModelSerializer):
    one_way_travel_time_min = serializers.FloatField(read_only=True)
    round_trip_travel_time_min = serializers.FloatField(read_only=True)
    cycle_time_min = serializers.FloatField(read_only=True)
    trips_per_truck_per_day = serializers.IntegerField(read_only=True)
    total_trips_per_day = serializers.IntegerField(read_only=True)
    total_tonnage_per_day = serializers.FloatField(read_only=True)

    class Meta:
        model = LogisticsScenario
        fields = '__all__'
