from rest_framework.routers import DefaultRouter
from .views import WardrobeItemViewSet, OutfitViewSet

router = DefaultRouter()
router.register("items", WardrobeItemViewSet, basename="wardrobe-item")
router.register("outfits", OutfitViewSet, basename="outfit")

urlpatterns = router.urls
