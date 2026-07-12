from django.conf import settings
from django.db import models

from wardrobe.models import WardrobeItem


class Recommendation(models.Model):
    """A saved, generated outfit suggestion. Generated via simple rule-based
    matching on category/season/occasion/color -- no ML involved."""

    SOURCE_CHOICES = [
        ("manual", "Manual Request"),
        ("weather", "Weather-Based (Travel Planner)"),
        ("occasion", "Occasion-Based"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recommendations")
    items = models.ManyToManyField(WardrobeItem, related_name="recommendations")
    occasion = models.CharField(max_length=20, choices=WardrobeItem.OCCASION_CHOICES, default="casual")
    season = models.CharField(max_length=20, choices=WardrobeItem.SEASON_CHOICES, default="all_season")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="manual")
    notes = models.TextField(blank=True, help_text="Human-readable explanation of why this outfit was suggested.")
    is_saved = models.BooleanField(default=False, help_text="Whether user explicitly saved this to history/favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Recommendation for {self.user.email} ({self.occasion}, {self.season})"
