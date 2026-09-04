from typing import Any, TypeVar

from rest_framework.serializers import IntegerField, Serializer

from common.pagination import PaginatedDTO, PaginationDTO


class PaginationSerializer(Serializer[PaginationDTO]):
    page = IntegerField()
    per_page = IntegerField()
    total = IntegerField()
    total_pages = IntegerField()


SerializerT = TypeVar("SerializerT", bound=Serializer[Any])


def paginated_serializer(
    item_serializer: type[SerializerT],
) -> type[Serializer[Any]]:
    """Create a serializer with ``data`` and ``pagination`` fields."""

    class PaginatedResponseSerializer(Serializer[PaginatedDTO[Any]]):
        data = item_serializer(many=True)  # type: ignore[assignment]
        pagination = PaginationSerializer()

    PaginatedResponseSerializer.__name__ = (
        f"Paginated{item_serializer.__name__}Serializer"
    )
    return PaginatedResponseSerializer
