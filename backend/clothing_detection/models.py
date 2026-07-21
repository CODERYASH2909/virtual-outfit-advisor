from django.conf import settings
from django.db import models


class ClothingImage(models.Model):
    """An uploaded image that has been processed by the clothing detector."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clothing_images",
    )
    image = models.ImageField(upload_to="clothing_uploads/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.original_filename} (by {self.user})"


class ClothingDetection(models.Model):
    """A single clothing item detected within a ClothingImage."""

    class Category(models.TextChoices):
        SHIRT = "Shirt", "Shirt"
        T_SHIRT = "T-Shirt", "T-Shirt"
        HOODIE = "Hoodie", "Hoodie"
        JACKET = "Jacket", "Jacket"
        BLAZER = "Blazer", "Blazer"
        SWEATER = "Sweater", "Sweater"
        JEANS = "Jeans", "Jeans"
        PANTS = "Pants", "Pants"
        SHORTS = "Shorts", "Shorts"
        SKIRT = "Skirt", "Skirt"
        DRESS = "Dress", "Dress"
        SHOES = "Shoes", "Shoes"
        SNEAKERS = "Sneakers", "Sneakers"
        SANDALS = "Sandals", "Sandals"
        CAP = "Cap", "Cap"
        HAT = "Hat", "Hat"
        BELT = "Belt", "Belt"
        BAG = "Bag", "Bag"

    image = models.ForeignKey(
        ClothingImage,
        on_delete=models.CASCADE,
        related_name="detections",
    )
    category = models.CharField(max_length=30, choices=Category.choices)
    confidence = models.FloatField(
        help_text="Detection confidence score between 0.0 and 1.0"
    )

    # Bounding-box coordinates (normalised or pixel — depends on the model).
    # Stored as absolute pixel coordinates from YOLO xyxy output.
    bbox_x1 = models.FloatField(help_text="Top-left X coordinate")
    bbox_y1 = models.FloatField(help_text="Top-left Y coordinate")
    bbox_x2 = models.FloatField(help_text="Bottom-right X coordinate")
    bbox_y2 = models.FloatField(help_text="Bottom-right Y coordinate")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-confidence"]
        indexes = [
            models.Index(fields=["image", "category"]),
        ]

    def __str__(self):
        return f"{self.category} ({self.confidence:.2f}) in {self.image.original_filename}"

    @property
    def bounding_box(self):
        """Return the bounding box as a list [x1, y1, x2, y2]."""
        return [self.bbox_x1, self.bbox_y1, self.bbox_x2, self.bbox_y2]
