from django.urls import path
from .views import UserTryOnPhotoView, GenerateTryOnView, TryOnResultListView

urlpatterns = [
    path("photo/", UserTryOnPhotoView.as_view(), name="tryon-photo"),
    path("generate/", GenerateTryOnView.as_view(), name="tryon-generate"),
    path("results/", TryOnResultListView.as_view(), name="tryon-results"),
]
