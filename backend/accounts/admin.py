from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, PasswordResetToken


@admin.register(User)
class VOAUserAdmin(UserAdmin):
    list_display = ("email", "username", "first_name", "last_name", "style_preference", "is_staff")
    search_fields = ("email", "username", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        ("VOA Profile", {"fields": (
            "phone_number", "avatar", "gender", "date_of_birth",
            "city", "country", "style_preference",
        )}),
    )


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "token", "created_at", "is_used")
    list_filter = ("is_used",)
