from django.contrib import admin
from .models import UserTryOnPhoto, TryOnResult


@admin.register(UserTryOnPhoto)
class UserTryOnPhotoAdmin(admin.ModelAdmin):
    list_display = ["user", "uploaded_at"]
    readonly_fields = ["uploaded_at"]
    raw_id_fields = ["user"]


@admin.register(TryOnResult)
class TryOnResultAdmin(admin.ModelAdmin):
    list_display = ["user", "recommendation", "created_at"]
    readonly_fields = ["created_at"]
    raw_id_fields = ["user", "recommendation"]
    list_filter = ["created_at"]
