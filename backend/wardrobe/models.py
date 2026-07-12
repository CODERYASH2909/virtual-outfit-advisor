from django.conf import settings
from django.db import models


class WardrobeItem(models.Model):
    CATEGORY_CHOICES = [
        ("top", "Top"),
        ("bottom", "Bottom"),
        ("dress", "Dress"),
        ("outerwear", "Outerwear"),
        ("footwear", "Footwear"),
        ("accessory", "Accessory"),
        ("headwear", "Headwear"),
        ("bag", "Bag"),
        ("innerwear", "Innerwear"),
        ("sportswear", "Sportswear"),
    ]

    SEASON_CHOICES = [
        ("summer", "Summer"),
        ("winter", "Winter"),
        ("spring", "Spring"),
        ("autumn", "Autumn"),
        ("all_season", "All Season"),
        ("rainy", "Rainy"),
    ]

    OCCASION_CHOICES = [
        ("casual", "Casual"),
        ("formal", "Formal"),
        ("business", "Business"),
        ("party", "Party"),
        ("sports", "Sports"),
        ("travel", "Travel"),
        ("beach", "Beach"),
        ("wedding", "Wedding"),
        ("loungewear", "Loungewear"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wardrobe_items")
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=40)
    secondary_color = models.CharField(max_length=40, blank=True)
    brand = models.CharField(max_length=80, blank=True)
    size = models.CharField(max_length=20, blank=True)
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default="all_season")
    occasion = models.CharField(max_length=20, choices=OCCASION_CHOICES, default="casual")
    material = models.CharField(max_length=80, blank=True)
    image = models.ImageField(upload_to="wardrobe/", blank=True, null=True)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    is_favorite = models.BooleanField(default=False)
    times_worn = models.PositiveIntegerField(default=0)
    last_worn_at = models.DateField(blank=True, null=True)
    purchase_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "category"]),
            models.Index(fields=["user", "season"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]


class Outfit(models.Model):
    """A saved combination of wardrobe items, created manually or from a recommendation."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="outfits")
    name = models.CharField(max_length=120)
    items = models.ManyToManyField(WardrobeItem, related_name="outfits")
    occasion = models.CharField(max_length=20, choices=WardrobeItem.OCCASION_CHOICES, default="casual")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
