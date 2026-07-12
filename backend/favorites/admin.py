from django.contrib import admin
from .models import FavoriteOutfit


@admin.register(FavoriteOutfit)
class FavoriteOutfitAdmin(admin.ModelAdmin):
    list_display = ("user", "outfit", "recommendation", "created_at")
