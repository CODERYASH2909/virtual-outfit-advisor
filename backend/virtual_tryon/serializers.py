from rest_framework import serializers
from .models import UserTryOnPhoto, TryOnResult


class UserTryOnPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTryOnPhoto
        fields = ["id", "photo", "processed_photo", "uploaded_at"]
        read_only_fields = ["id", "processed_photo", "uploaded_at"]


class TryOnResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TryOnResult
        fields = ["id", "recommendation", "result_image", "created_at"]
        read_only_fields = fields


class GenerateTryOnRequestSerializer(serializers.Serializer):
    recommendation_id = serializers.IntegerField(
        help_text="ID of the recommendation whose outfit should be tried on."
    )
