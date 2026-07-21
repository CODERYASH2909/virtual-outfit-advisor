import logging

from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .detector import ClothingDetector
from .models import ClothingImage, ClothingDetection
from .serializers import (
    ClothingImageListSerializer,
    ClothingImageSerializer,
    ClothingUploadSerializer,
)

logger = logging.getLogger(__name__)


class UploadClothingView(APIView):
    """
    POST /api/clothing/upload-clothing/

    Upload an image → run YOLO clothing detection → save results →
    return the full detection response.

    Accepts ``multipart/form-data`` with an ``image`` field.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # ── 1. Validate the upload ────────────────────────────────────
        serializer = ClothingUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_file = serializer.validated_data["image"]

        # ── 2. Persist the image ──────────────────────────────────────
        clothing_image = ClothingImage.objects.create(
            user=request.user,
            image=image_file,
            original_filename=image_file.name,
        )

        # ── 3. Run YOLO inference ─────────────────────────────────────
        detector = ClothingDetector.get_instance()
        image_path = clothing_image.image.path  # absolute filesystem path

        try:
            raw_detections = detector.detect(image_path)
        except Exception:
            logger.exception(
                "YOLO inference failed for image %s", clothing_image.id
            )
            # Keep the image record but return an error.
            return Response(
                {
                    "success": False,
                    "errors": {"detail": "Clothing detection failed. Please try again."},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ── 4. Bulk-create detection rows ─────────────────────────────
        detection_objects = [
            ClothingDetection(
                image=clothing_image,
                category=det["category"],
                confidence=det["confidence"],
                bbox_x1=det["bounding_box"][0],
                bbox_y1=det["bounding_box"][1],
                bbox_x2=det["bounding_box"][2],
                bbox_y2=det["bounding_box"][3],
            )
            for det in raw_detections
        ]
        ClothingDetection.objects.bulk_create(detection_objects)

        # ── 5. Return the full result ─────────────────────────────────
        # Re-fetch to include the freshly created detections via the ORM.
        clothing_image.refresh_from_db()
        response_serializer = ClothingImageSerializer(
            clothing_image, context={"request": request}
        )

        return Response(
            {
                "success": True,
                "data": response_serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class ClothingDetailView(generics.RetrieveAPIView):
    """
    GET /api/clothing/{id}/

    Retrieve a specific clothing image with all its detected items.
    Scoped to the authenticated user.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClothingImageSerializer

    def get_queryset(self):
        return ClothingImage.objects.filter(user=self.request.user).prefetch_related(
            "detections"
        )


class ClothingListView(generics.ListAPIView):
    """
    GET /api/clothing/list/

    List all clothing images uploaded by the authenticated user.
    Uses the lightweight list serializer (detection count only).
    Paginated via the project-wide ``StandardResultsSetPagination``.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ClothingImageListSerializer

    def get_queryset(self):
        return ClothingImage.objects.filter(user=self.request.user)
