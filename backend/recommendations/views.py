from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.mixins import OwnerQuerysetMixin
from .models import Recommendation
from .serializers import RecommendationSerializer, RecommendationRequestSerializer
from .services import build_outfit
from travel.services import WeatherAPIError, fetch_weather_forecast, infer_season_from_temp


def infer_weather_season(weather):
    condition = weather["weather_condition"]
    if condition in {"Rain", "Drizzle", "Thunderstorm"}:
        return "rainy"
    return infer_season_from_temp(weather["avg_temperature_c"])


def build_weather_note(weather, city):
    temp = weather["avg_temperature_c"]
    season = infer_weather_season(weather)
    if temp >= 25:
        advice = "Hot weather detected, so VOA prioritized relaxed, breathable wardrobe pieces."
    elif temp <= 10:
        advice = "Low temperature detected, so VOA prioritized warmer layered clothing."
    else:
        advice = "Mild weather detected, so VOA prioritized comfortable everyday layers."
    return (
        f"Weather in {city}: {weather['weather_condition']}, about {temp}C on average. "
        f"{advice} Matched as {season.replace('_', ' ')}."
    )


class GenerateRecommendationView(APIView):
    """Generates a new rule-based outfit recommendation and stores it in history."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        req = RecommendationRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        season = req.validated_data["season"]
        occasion = req.validated_data["occasion"]
        city = req.validated_data.get("city", "").strip()
        country = req.validated_data.get("country", "").strip()
        latitude = req.validated_data.get("latitude")
        longitude = req.validated_data.get("longitude")
        source = "occasion"
        weather_note = ""

        if (latitude is not None and longitude is not None) or city:
            try:
                weather = fetch_weather_forecast(city, country, lat=latitude, lon=longitude)
            except WeatherAPIError as exc:
                return Response({"success": False, "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            
            if latitude is not None and longitude is not None:
                city = weather.get("city", city)
                country = weather.get("country", country)
                if not city:
                    city = "Detected Location"

            season = infer_weather_season(weather)
            source = "weather"
            weather_note = build_weather_note(weather, city)

        items, explanation = build_outfit(request.user, season=season, occasion=occasion)
        if items is None:
            return Response({"success": False, "message": explanation}, status=status.HTTP_400_BAD_REQUEST)
        if weather_note:
            explanation = f"{weather_note} {explanation}"

        recommendation = Recommendation.objects.create(
            user=request.user, occasion=occasion, season=season,
            source=source, notes=explanation,
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
