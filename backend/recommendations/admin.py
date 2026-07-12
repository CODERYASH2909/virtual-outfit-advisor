from django.contrib import admin
from .models import Recommendation


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("user", "occasion", "season", "source", "is_saved", "created_at")
    list_filter = ("occasion", "season", "source", "is_saved")
