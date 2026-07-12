from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import GenerateRecommendationView, RecommendationHistoryViewSet

router = DefaultRouter()
router.register("history", RecommendationHistoryViewSet, basename="recommendation-history")

urlpatterns = [
    path("generate/", GenerateRecommendationView.as_view(), name="generate-recommendation"),
] + router.urls
