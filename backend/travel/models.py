from django.conf import settings
from django.db import models


class TravelPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="travel_plans")
    destination_city = models.CharField(max_length=120)
    destination_country = models.CharField(max_length=120, blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    trip_purpose = models.CharField(
        max_length=20,
        choices=[
            ("leisure", "Leisure"), ("business", "Business"), ("adventure", "Adventure"),
            ("beach", "Beach"), ("city_break", "City Break"), ("winter_sports", "Winter Sports"),
        ],
        default="leisure",
    )
    # Snapshot of the weather data fetched from the Weather API at planning time.
    avg_temperature_c = models.FloatField(blank=True, null=True)
    min_temperature_c = models.FloatField(blank=True, null=True)
    max_temperature_c = models.FloatField(blank=True, null=True)
    weather_condition = models.CharField(max_length=60, blank=True)
    weather_summary = models.TextField(blank=True)
    packing_list = models.JSONField(default=list, blank=True)
    outfit_suggestions = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.destination_city} trip ({self.start_date} - {self.end_date})"
