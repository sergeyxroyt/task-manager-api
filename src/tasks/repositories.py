from collections.abc import Sequence

from common.pagination import PaginatedDTO, build_pagination

from .exceptions import TaskNotFoundError
from .models import Task


class TaskRepository:
    def list(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Sequence[str] = (),
    ) -> PaginatedDTO[Task]:
        queryset = Task.objects.all()
        if statuses:
            queryset = queryset.filter(status__in=statuses)

        total = queryset.count()
        return PaginatedDTO(
            data=list(queryset[offset : offset + limit]),
            pagination=build_pagination(limit=limit, offset=offset, total=total),
        )

    def get_by_id(self, task_id: int) -> Task:
        try:
            return Task.objects.get(pk=task_id)
        except Task.DoesNotExist as exc:
            raise TaskNotFoundError from exc
