import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for VOA. Email is the primary unique identifier."""

    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    gender = models.CharField(
        max_length=20,
        choices=[("male", "Male"), ("female", "Female"), ("other", "Other"), ("prefer_not_to_say", "Prefer not to say")],
        blank=True,
        default="prefer_not_to_say",
    )
    date_of_birth = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    style_preference = models.CharField(
        max_length=30,
        choices=[
            ("casual", "Casual"),
            ("formal", "Formal"),
            ("streetwear", "Streetwear"),
            ("business", "Business"),
            ("sporty", "Sporty"),
            ("bohemian", "Bohemian"),
            ("minimalist", "Minimalist"),
        ],
        blank=True,
        default="casual",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class PasswordResetToken(models.Model):
    """One-time token used to authorize a password reset request."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Reset token for {self.user.email}"
