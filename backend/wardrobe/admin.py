from django.contrib import admin
from .models import WardrobeItem, Outfit


@admin.register(WardrobeItem)
class WardrobeItemAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "category", "color", "season", "occasion", "is_favorite", "times_worn")
    list_filter = ("category", "season", "occasion", "is_favorite")
    search_fields = ("name", "brand", "color", "tags")


@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "occasion", "created_at")
    filter_horizontal = ("items",)
