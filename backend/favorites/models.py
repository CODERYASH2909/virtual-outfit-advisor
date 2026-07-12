from django.conf import settings
from django.db import models

from wardrobe.models import WardrobeItem, Outfit
from recommendations.models import Recommendation


class FavoriteOutfit(models.Model):
    """A favorited outfit or recommendation, unified so the Favorites page
    can list both saved outfits and saved recommendations together."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_outfits")
    outfit = models.ForeignKey(Outfit, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by")
    recommendation = models.ForeignKey(
        Recommendation, on_delete=models.CASCADE, null=True, blank=True, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "outfit"], name="unique_user_outfit_favorite"),
            models.UniqueConstraint(fields=["user", "recommendation"], name="unique_user_recommendation_favorite"),
        ]

    def __str__(self):
        target = self.outfit or self.recommendation
        return f"Favorite: {target} ({self.user.email})"
