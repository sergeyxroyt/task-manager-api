from typing import Any, TypeVar

from rest_framework import serializers

from .pagination import PaginatedDTO, PaginationDTO


class PaginationSerializer(serializers.Serializer[PaginationDTO]):
    page = serializers.IntegerField()
    per_page = serializers.IntegerField()
    total = serializers.IntegerField()
    total_pages = serializers.IntegerField()


SerializerT = TypeVar("SerializerT", bound=serializers.Serializer[Any])


def paginated_serializer(
    item_serializer: type[SerializerT],
) -> type[serializers.Serializer[Any]]:
    """Build a response serializer for any ``PaginatedDTO`` item type."""

    class PaginatedResponseSerializer(serializers.Serializer[PaginatedDTO[Any]]):
        data = item_serializer(many=True)  # type: ignore[assignment]
        pagination = PaginationSerializer()

    PaginatedResponseSerializer.__name__ = (
        f"Paginated{item_serializer.__name__}Serializer"
    )
    return PaginatedResponseSerializer
