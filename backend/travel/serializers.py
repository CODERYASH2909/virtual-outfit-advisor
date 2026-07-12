from rest_framework import serializers
from .models import TravelPlan


class TravelPlanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = ["id", "destination_city", "destination_country", "start_date", "end_date", "trip_purpose"]

    def validate(self, attrs):
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        return attrs


class TravelPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelPlan
        fields = [
            "id", "destination_city", "destination_country", "start_date", "end_date",
            "trip_purpose", "avg_temperature_c", "min_temperature_c", "max_temperature_c",
            "weather_condition", "weather_summary", "packing_list", "outfit_suggestions",
            "created_at", "updated_at",
        ]
        read_only_fields = fields
