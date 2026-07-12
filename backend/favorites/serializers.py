from rest_framework import serializers
from .models import FavoriteOutfit
from wardrobe.serializers import OutfitSerializer
from recommendations.serializers import RecommendationSerializer


class FavoriteOutfitSerializer(serializers.ModelSerializer):
    outfit_detail = OutfitSerializer(source="outfit", read_only=True)
    recommendation_detail = RecommendationSerializer(source="recommendation", read_only=True)

    class Meta:
        model = FavoriteOutfit
        fields = ["id", "outfit", "recommendation", "outfit_detail", "recommendation_detail", "created_at"]
        read_only_fields = ["id", "created_at"]
        extra_kwargs = {"outfit": {"write_only": True}, "recommendation": {"write_only": True}}

    def validate(self, attrs):
        if not attrs.get("outfit") and not attrs.get("recommendation"):
            raise serializers.ValidationError("Provide either an outfit or a recommendation to favorite.")
        if attrs.get("outfit") and attrs.get("recommendation"):
            raise serializers.ValidationError("Favorite either an outfit or a recommendation, not both.")
        return attrs
