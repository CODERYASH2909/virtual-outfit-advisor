import os

from rest_framework import serializers

from .models import ClothingImage, ClothingDetection


class ClothingUploadSerializer(serializers.Serializer):
    """Validates the uploaded image for clothing detection."""

    image = serializers.ImageField()

    def validate_image(self, value):
        # ── File-size check ────────────────────────────────────────────
        from django.conf import settings

        max_mb = getattr(settings, "CLOTHING_DETECTION", {}).get(
            "MAX_IMAGE_SIZE_MB", 10
        )
        max_bytes = max_mb * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError(
                f"Image file too large. Maximum allowed size is {max_mb} MB."
            )

        # ── Extension check ───────────────────────────────────────────
        allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported image format '{ext}'. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}."
            )

        return value


class ClothingDetectionSerializer(serializers.ModelSerializer):
    """Read-only serializer for a single detected clothing item."""

    bounding_box = serializers.SerializerMethodField()

    class Meta:
        model = ClothingDetection
        fields = ["id", "category", "confidence", "bounding_box"]
        read_only_fields = fields

    def get_bounding_box(self, obj) -> list[float]:
        return obj.bounding_box


class ClothingImageSerializer(serializers.ModelSerializer):
    """Full detail serializer for a clothing image with all detections."""

    detections = ClothingDetectionSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ClothingImage
        fields = [
            "id",
            "image",
            "image_url",
            "original_filename",
            "detections",
            "created_at",
        ]
        read_only_fields = fields

    def get_image_url(self, obj) -> str | None:
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class ClothingImageListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer — detection count instead of full nesting."""

    detection_count = serializers.IntegerField(
        source="detections.count", read_only=True
    )
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ClothingImage
        fields = [
            "id",
            "image_url",
            "original_filename",
            "detection_count",
            "created_at",
        ]
        read_only_fields = fields

    def get_image_url(self, obj) -> str | None:
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None
