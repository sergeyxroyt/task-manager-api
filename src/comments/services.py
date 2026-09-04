from common.pagination import PaginatedDTO
from tasks.repositories import TaskRepository

from .models import Comment
from .repositories import CommentRepository


class CommentService:
    def __init__(
        self,
        repository: CommentRepository | None = None,
        task_repository: TaskRepository | None = None,
    ) -> None:
        self.repository = repository or CommentRepository()
        self.task_repository = task_repository or TaskRepository()

    def list_by_task(
        self, *, task_id: int, limit: int, offset: int
    ) -> PaginatedDTO[Comment]:
        self.task_repository.get_by_id(task_id)
        return self.repository.list_by_task(task_id=task_id, limit=limit, offset=offset)
