from dataclasses import dataclass
from typing import Generic, TypeVar


ItemT = TypeVar("ItemT")


@dataclass(frozen=True, slots=True)
class PaginationDTO:
    page: int
    per_page: int
    total: int
    total_pages: int


@dataclass(frozen=True, slots=True)
class PaginatedDTO(Generic[ItemT]):
    data: list[ItemT]
    pagination: PaginationDTO


def build_pagination(*, limit: int, offset: int, total: int) -> PaginationDTO:
    """Build metadata for offset pagination with one-based page numbering."""
    return PaginationDTO(
        page=offset // limit + 1,
        per_page=limit,
        total=total,
        total_pages=(total + limit - 1) // limit,
    )
