from django.contrib import admin
from .models import TravelPlan


@admin.register(TravelPlan)
class TravelPlanAdmin(admin.ModelAdmin):
    list_display = ("user", "destination_city", "start_date", "end_date", "weather_condition", "avg_temperature_c")
    search_fields = ("destination_city", "destination_country")
