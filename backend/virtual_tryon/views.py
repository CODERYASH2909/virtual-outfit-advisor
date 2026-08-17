import logging
from pathlib import Path

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendations.models import Recommendation
from .models import UserTryOnPhoto, TryOnResult
from .serializers import (
    UserTryOnPhotoSerializer,
    TryOnResultSerializer,
    GenerateTryOnRequestSerializer,
)
from .services import run_virtual_tryon, map_category_to_cloth_type, get_or_create_processed_photo

logger = logging.getLogger(__name__)


class UserTryOnPhotoView(APIView):
    """Manage the user's full-body photo for Virtual Try-On.

    GET    → retrieve current photo (or 404)
    POST   → upload / replace photo (triggers single-time base character preprocessing)
    DELETE → delete photo
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        try:
            photo = request.user.tryon_photo
            return Response(UserTryOnPhotoSerializer(photo).data)
        except UserTryOnPhoto.DoesNotExist:
            return Response(
                {"detail": "No photo uploaded yet."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def post(self, request):
        photo_file = request.FILES.get("photo")
        if not photo_file:
            return Response(
                {"detail": "No photo file provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file type.
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if photo_file.content_type not in allowed_types:
            return Response(
                {"detail": "Only JPEG, PNG, and WebP images are accepted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate file size (max 10 MB).
        max_size = 10 * 1024 * 1024
        if photo_file.size > max_size:
            return Response(
                {"detail": "Photo must be smaller than 10 MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photo_obj, created = UserTryOnPhoto.objects.update_or_create(
            user=request.user,
            defaults={"photo": photo_file, "processed_photo": None},
        )

        # Build permanent base character photo ONCE upon upload
        try:
            get_or_create_processed_photo(photo_obj)
            photo_obj.refresh_from_db()
        except Exception as exc:
            logger.warning("Single-time base character preprocessing failed on upload (%s)", exc)

        return Response(
            UserTryOnPhotoSerializer(photo_obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request):
        try:
            photo = request.user.tryon_photo
            if photo.photo:
                photo.photo.delete(save=False)
            if photo.processed_photo:
                photo.processed_photo.delete(save=False)
            photo.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserTryOnPhoto.DoesNotExist:
            return Response(
                {"detail": "No photo to delete."},
                status=status.HTTP_404_NOT_FOUND,
            )


class GenerateTryOnView(APIView):
    """Generate a Virtual Try-On preview for a recommendation.

    POST  body: { "recommendation_id": <int> }

    Flow:
      1. Validate that the user has an uploaded photo.
      2. Fetch the recommendation and its clothing items.
      3. Reuse the saved permanent base character photo.
      4. Call CatVTON for each garment item in priority order.
      5. Save and return composite result.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = GenerateTryOnRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        rec_id = serializer.validated_data["recommendation_id"]

        # 1. Check user photo.
        try:
            photo_obj = request.user.tryon_photo
        except UserTryOnPhoto.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "message": "Please upload your photo first to use Virtual Try-On.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Fetch recommendation.
        try:
            recommendation = Recommendation.objects.get(
                id=rec_id, user=request.user
            )
        except Recommendation.DoesNotExist:
            return Response(
                {"success": False, "message": "Recommendation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 3. Build garment list from recommendation items.
        items = recommendation.items.all()
        garment_items = []
        for item in items:
            cloth_type = map_category_to_cloth_type(item.category)
            if cloth_type and item.image:
                garment_items.append(
                    {
                        "name": item.name,
                        "category": item.category,
                        "image_path": item.image.path,
                    }
                )

        if not garment_items:
            return Response(
                {
                    "success": False,
                    "message": "None of the outfit items have images suitable for Virtual Try-On. "
                    "Please ensure your wardrobe items have photos uploaded.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 4. Run try-on using saved permanent base character photo.
        try:
            result_path, items_processed = run_virtual_tryon(photo_obj, garment_items)
        except (ValueError, RuntimeError) as exc:
            logger.error("Virtual Try-On failed: %s", exc)
            return Response(
                {"success": False, "message": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 5. Save the result.
        relative_path = Path(result_path).relative_to(settings.MEDIA_ROOT)
        result_obj = TryOnResult.objects.create(
            user=request.user,
            recommendation=recommendation,
            result_image=str(relative_path),
        )

        return Response(
            {
                "success": True,
                "result": TryOnResultSerializer(result_obj).data,
                "items_processed": items_processed,
            },
            status=status.HTTP_201_CREATED,
        )


class TryOnResultListView(APIView):
    """List past try-on results for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        results = TryOnResult.objects.filter(user=request.user)[:20]
        return Response(TryOnResultSerializer(results, many=True).data)
