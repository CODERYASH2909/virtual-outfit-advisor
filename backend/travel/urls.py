from rest_framework.routers import DefaultRouter
from .views import TravelPlanViewSet

router = DefaultRouter()
router.register("plans", TravelPlanViewSet, basename="travel-plan")

urlpatterns = router.urls
