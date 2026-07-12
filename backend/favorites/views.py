from rest_framework import viewsets, permissions
from core.mixins import OwnerQuerysetMixin
from .models import FavoriteOutfit
from .serializers import FavoriteOutfitSerializer


class FavoriteOutfitViewSet(OwnerQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = FavoriteOutfitSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = FavoriteOutfit.objects.all()
