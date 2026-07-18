from rest_framework import serializers
from .models import Recommendation
from wardrobe.serializers import WardrobeItemMiniSerializer


class RecommendationRequestSerializer(serializers.Serializer):
    season = serializers.ChoiceField(
        choices=["summer", "winter", "spring", "autumn", "all_season", "rainy"],
        required=False, default="all_season",
    )
    occasion = serializers.ChoiceField(
        choices=["casual", "formal", "business", "party", "sports", "travel", "beach", "wedding", "loungewear"],
        required=False, default="casual",
    )
    city = serializers.CharField(required=False, allow_blank=True, max_length=120)
    country = serializers.CharField(required=False, allow_blank=True, max_length=120)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)


class RecommendationSerializer(serializers.ModelSerializer):
    items_detail = WardrobeItemMiniSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = Recommendation
        fields = [
            "id", "items_detail", "occasion", "season", "source",
            "notes", "is_saved", "created_at",
        ]
        read_only_fields = fields
