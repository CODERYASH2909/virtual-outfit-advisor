from django.contrib import admin

from .models import ClothingDetection, ClothingImage


class ClothingDetectionInline(admin.TabularInline):
    model = ClothingDetection
    extra = 0
    readonly_fields = [
        "category",
        "confidence",
        "bbox_x1",
        "bbox_y1",
        "bbox_x2",
        "bbox_y2",
        "created_at",
    ]


@admin.register(ClothingImage)
class ClothingImageAdmin(admin.ModelAdmin):
    list_display = ["id", "original_filename", "user", "detection_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["original_filename", "user__email"]
    readonly_fields = ["created_at"]
    inlines = [ClothingDetectionInline]

    def detection_count(self, obj):
        return obj.detections.count()

    detection_count.short_description = "Detections"


@admin.register(ClothingDetection)
class ClothingDetectionAdmin(admin.ModelAdmin):
    list_display = ["id", "category", "confidence", "image", "created_at"]
    list_filter = ["category", "created_at"]
    search_fields = ["category", "image__original_filename"]
    readonly_fields = ["created_at"]
