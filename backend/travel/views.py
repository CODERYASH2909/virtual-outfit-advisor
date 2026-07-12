from datetime import date
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response

from core.mixins import OwnerQuerysetMixin
from .models import TravelPlan
from .serializers import TravelPlanCreateSerializer, TravelPlanSerializer
from .services import (
    fetch_weather_forecast, infer_season_from_temp, build_packing_list,
    build_outfit_suggestions_from_wardrobe, WeatherAPIError,
)


class TravelPlanViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = TravelPlan.objects.all()
    ordering_fields = ["start_date", "created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return TravelPlanCreateSerializer
        return TravelPlanSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            weather = fetch_weather_forecast(data["destination_city"], data.get("destination_country", ""))
        except WeatherAPIError as exc:
            return Response({"success": False, "message": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        season = infer_season_from_temp(weather["avg_temperature_c"])
        duration_days = (data["end_date"] - data["start_date"]).days + 1
        packing_list = build_packing_list(
            weather["avg_temperature_c"], weather["weather_condition"], data["trip_purpose"], duration_days
        )
        outfit_suggestions = build_outfit_suggestions_from_wardrobe(request.user, season)

        plan = TravelPlan.objects.create(
            user=request.user,
            destination_city=data["destination_city"],
            destination_country=data.get("destination_country", ""),
            start_date=data["start_date"],
            end_date=data["end_date"],
            trip_purpose=data["trip_purpose"],
            avg_temperature_c=weather["avg_temperature_c"],
            min_temperature_c=weather["min_temperature_c"],
            max_temperature_c=weather["max_temperature_c"],
            weather_condition=weather["weather_condition"],
            weather_summary=weather["weather_summary"],
            packing_list=packing_list,
            outfit_suggestions=outfit_suggestions,
        )
        return Response(TravelPlanSerializer(plan).data, status=status.HTTP_201_CREATED)
