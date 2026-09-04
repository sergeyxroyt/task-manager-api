from collections.abc import Sequence

from common.pagination import PaginatedDTO

from .models import Task
from .repositories import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository | None = None) -> None:
        self.repository = repository or TaskRepository()

    def list(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Sequence[str] = (),
    ) -> PaginatedDTO[Task]:
        return self.repository.list(limit=limit, offset=offset, statuses=statuses)

    def get_by_id(self, task_id: int) -> Task:
        return self.repository.get_by_id(task_id)
