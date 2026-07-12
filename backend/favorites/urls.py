from rest_framework.routers import DefaultRouter
from .views import FavoriteOutfitViewSet

router = DefaultRouter()
router.register("", FavoriteOutfitViewSet, basename="favorite")

urlpatterns = router.urls
