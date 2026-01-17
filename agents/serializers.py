"""
Serializers for agent API endpoints.
"""
from rest_framework import serializers


class GeminiCostRequestSerializer(serializers.Serializer):
    """Serializer for Gemini Cost Agent request."""
    delay_hours = serializers.IntegerField(min_value=0)
    total_passengers = serializers.IntegerField(min_value=0)
    vip_passengers = serializers.IntegerField(min_value=0)

    def validate(self, data):
        """Validate that VIP passengers don't exceed total passengers."""
        if data['vip_passengers'] > data['total_passengers']:
            raise serializers.ValidationError(
                "VIP passengers cannot exceed total passengers"
            )
        return data


class ComplianceRequestSerializer(serializers.Serializer):
    """Serializer for Compliance Agent request."""
    delay_hours = serializers.IntegerField(min_value=0)


class OpsRequestSerializer(serializers.Serializer):
    """Serializer for Ops Agent request (optional fields)."""
    pass


class AgentResponseSerializer(serializers.Serializer):
    """Base serializer for agent responses."""
    agent = serializers.CharField()
    recommendation = serializers.CharField(required=False)
    reason = serializers.CharField(required=False)
    confidence = serializers.FloatField(required=False, min_value=0.0, max_value=1.0)
    rule = serializers.CharField(required=False)
    available_seats = serializers.IntegerField(required=False)
    hotel_capacity = serializers.CharField(required=False)
