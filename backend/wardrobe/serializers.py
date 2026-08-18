from rest_framework import serializers
from .models import WardrobeItem, Outfit


class WardrobeItemSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    season_display = serializers.CharField(source="get_season_display", read_only=True)
    occasion_display = serializers.CharField(source="get_occasion_display", read_only=True)
    tag_list = serializers.SerializerMethodField()

    class Meta:
        model = WardrobeItem
        fields = [
            "id", "name", "category", "category_display", "color", "secondary_color",
            "brand", "size", "season", "season_display", "occasion", "occasion_display",
            "material", "image", "notes", "tags", "tag_list", "is_favorite",
            "times_worn", "last_worn_at", "purchase_date", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "times_worn"]

    def get_tag_list(self, obj):
        return obj.tag_list()


class WardrobeItemMiniSerializer(serializers.ModelSerializer):
    """Lightweight representation used when nesting items inside outfits/recommendations."""

    class Meta:
        model = WardrobeItem
        fields = ["id", "name", "category", "color", "image", "season", "occasion"]


class OutfitSerializer(serializers.ModelSerializer):
    items_detail = WardrobeItemMiniSerializer(source="items", many=True, read_only=True)
    item_ids = serializers.PrimaryKeyRelatedField(
        source="items", queryset=WardrobeItem.objects.all(), many=True, write_only=True
    )

    class Meta:
        model = Outfit
        fields = ["id", "name", "occasion", "notes", "items_detail", "item_ids", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_item_ids(self, value):
        request = self.context["request"]
        for item in value:
            if item.user_id != request.user.id:
                raise serializers.ValidationError("You can only add your own wardrobe items to an outfit.")
        return value
