from django.urls import path

from .views import ClothingDetailView, ClothingListView, UploadClothingView

urlpatterns = [
    path("upload-clothing/", UploadClothingView.as_view(), name="upload-clothing"),
    path("list/", ClothingListView.as_view(), name="clothing-list"),
    path("<int:pk>/", ClothingDetailView.as_view(), name="clothing-detail"),
]
