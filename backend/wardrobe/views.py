from django.utils import timezone
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from clothing_detection.isolation import isolate_garment
from core.mixins import OwnerQuerysetMixin
from .models import WardrobeItem, Outfit
from .serializers import WardrobeItemSerializer, OutfitSerializer
from .filters import WardrobeItemFilter


class WardrobeItemViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = WardrobeItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = WardrobeItem.objects.all()
    filterset_class = WardrobeItemFilter
    search_fields = ["name", "brand", "color", "tags", "notes"]
    ordering_fields = ["created_at", "name", "times_worn", "last_worn_at"]

    def perform_create(self, serializer):
        item = serializer.save(user=self.request.user)
        if item.image and item.image.storage.exists(item.image.name):
            item.original_image = item.image.name
            item.save(update_fields=["original_image"])

            success, message, clean_path, auto_category = isolate_garment(item.original_image.path)
            if not success:
                # Delete newly created object if garment isolation fails
                item.delete()
                raise serializers.ValidationError({"image": [message]})

            item.image = clean_path
            if auto_category and not serializer.validated_data.get("category"):
                item.category = auto_category
            item.save(update_fields=["image", "category"])

    def perform_update(self, serializer):
        item = serializer.save()
        if "image" in self.request.FILES:
            if item.image and item.image.storage.exists(item.image.name):
                item.original_image = item.image.name
                item.save(update_fields=["original_image"])

                success, message, clean_path, _ = isolate_garment(item.original_image.path)
                if not success:
                    raise serializers.ValidationError({"image": [message]})

                item.image = clean_path
                item.save(update_fields=["image"])

    @action(detail=True, methods=["post"])
    def mark_worn(self, request, pk=None):
        item = self.get_object()
        item.times_worn += 1
        item.last_worn_at = timezone.now().date()
        item.save(update_fields=["times_worn", "last_worn_at"])
        return Response(self.get_serializer(item).data)

    @action(detail=True, methods=["post"])
    def toggle_favorite(self, request, pk=None):
        item = self.get_object()
        item.is_favorite = not item.is_favorite
        item.save(update_fields=["is_favorite"])
        return Response(self.get_serializer(item).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        qs = self.get_queryset()
        by_category = {}
        for choice, label in WardrobeItem.CATEGORY_CHOICES:
            by_category[choice] = qs.filter(category=choice).count()
        return Response({
            "total_items": qs.count(),
            "favorites": qs.filter(is_favorite=True).count(),
            "by_category": by_category,
            "never_worn": qs.filter(times_worn=0).count(),
        })


class OutfitViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = OutfitSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Outfit.objects.all()
    search_fields = ["name", "notes"]
    ordering_fields = ["created_at", "name"]
