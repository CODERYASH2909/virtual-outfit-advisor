from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import OwnerQuerysetMixin
from .models import Recommendation
from .serializers import RecommendationSerializer, RecommendationRequestSerializer
from .services import build_outfit


class GenerateRecommendationView(APIView):
    """Generates a new rule-based outfit recommendation and stores it in history."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        req = RecommendationRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        season = req.validated_data["season"]
        occasion = req.validated_data["occasion"]

        items, explanation = build_outfit(request.user, season=season, occasion=occasion)
        if items is None:
            return Response({"success": False, "message": explanation}, status=status.HTTP_400_BAD_REQUEST)

        recommendation = Recommendation.objects.create(
            user=request.user, occasion=occasion, season=season,
            source="occasion", notes=explanation,
        )
        recommendation.items.set(items)
        return Response(
            {"success": True, "recommendation": RecommendationSerializer(recommendation).data},
            status=status.HTTP_201_CREATED,
        )


class RecommendationHistoryViewSet(OwnerQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only history of all previously generated recommendations."""
    serializer_class = RecommendationSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Recommendation.objects.all()
    filterset_fields = ["occasion", "season", "source", "is_saved"]
    ordering_fields = ["created_at"]

    @action(detail=True, methods=["post"])
    def save(self, request, pk=None):
        rec = self.get_object()
        rec.is_saved = True
        rec.save(update_fields=["is_saved"])
        return Response(self.get_serializer(rec).data)

    @action(detail=True, methods=["delete"], url_path="delete")
    def delete_entry(self, request, pk=None):
        rec = self.get_object()
        rec.delete()
        return Response(status=204)
