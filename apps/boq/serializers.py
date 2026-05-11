from rest_framework import serializers
from .models import BOQItem, DailyProgressRecord, PaymentClaim


class BOQItemSerializer(serializers.ModelSerializer):
    contract_amount = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    cumulative_quantity = serializers.DecimalField(max_digits=15, decimal_places=3, read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=15, decimal_places=3, read_only=True)
    percent_complete = serializers.FloatField(read_only=True)
    earned_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    project_name = serializers.CharField(source='project.project_name', read_only=True)

    class Meta:
        model = BOQItem
        fields = '__all__'


class DailyProgressRecordSerializer(serializers.ModelSerializer):
    boq_item_description = serializers.CharField(source='boq_item.description', read_only=True)

    class Meta:
        model = DailyProgressRecord
        fields = '__all__'


class PaymentClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentClaim
        fields = '__all__'
