class OwnerQuerysetMixin:
    """Restrict a ViewSet's queryset to objects owned by the requesting user."""

    owner_field = "user"

    def get_queryset(self):
        base_qs = super().get_queryset()
        return base_qs.filter(**{self.owner_field: self.request.user})

    def perform_create(self, serializer):
        serializer.save(**{self.owner_field: self.request.user})
