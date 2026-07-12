import django_filters
from .models import WardrobeItem


class WardrobeItemFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name="category")
    season = django_filters.CharFilter(field_name="season")
    occasion = django_filters.CharFilter(field_name="occasion")
    color = django_filters.CharFilter(field_name="color", lookup_expr="icontains")
    brand = django_filters.CharFilter(field_name="brand", lookup_expr="icontains")
    is_favorite = django_filters.BooleanFilter(field_name="is_favorite")
    min_times_worn = django_filters.NumberFilter(field_name="times_worn", lookup_expr="gte")

    class Meta:
        model = WardrobeItem
        fields = ["category", "season", "occasion", "color", "brand", "is_favorite"]
