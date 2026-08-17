from django.conf import settings
from django.db import models


class UserTryOnPhoto(models.Model):
    """The user's full-body photo used as the base for Virtual Try-On previews.

    Each user may have at most one photo stored at a time. Uploading a new
    photo replaces the previous one.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tryon_photo",
    )
    photo = models.ImageField(upload_to="tryon_photos/")
    processed_photo = models.ImageField(
        upload_to="tryon_processed/", null=True, blank=True
    )
    uploaded_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Try-On Photo"
        verbose_name_plural = "User Try-On Photos"

    def __str__(self):
        return f"Try-On Photo for {self.user.email}"


class TryOnResult(models.Model):
    """A generated Virtual Try-On preview image.

    Stores the composite result so that repeated requests for the same
    recommendation + photo pair can be served from cache.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tryon_results",
    )
    recommendation = models.ForeignKey(
        "recommendations.Recommendation",
        on_delete=models.CASCADE,
        related_name="tryon_results",
    )
    result_image = models.ImageField(upload_to="tryon_results/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Try-On Result"
        verbose_name_plural = "Try-On Results"

    def __str__(self):
        return f"Try-On #{self.pk} for {self.user.email}"
