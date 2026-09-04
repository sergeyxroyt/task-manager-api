from common.pagination import PaginatedDTO
from users.models import User
from tasks.repositories import TaskRepository

from comments.models import Comment
from comments.repositories import CommentRepository


class CommentService:
    def __init__(
        self,
        repository: CommentRepository | None = None,
        task_repository: TaskRepository | None = None,
    ) -> None:
        self.repository = repository or CommentRepository()
        self.task_repository = task_repository or TaskRepository()

    def create(self, *, task_id: int, author: User, content: str) -> Comment:
        """Create a comment after ensuring that its task exists."""
        self.task_repository.get_by_id(task_id)
        return self.repository.create(
            task_id=task_id,
            author=author,
            content=content,
        )

    def list_by_task(
        self, *, task_id: int, limit: int, offset: int
    ) -> PaginatedDTO[Comment]:
        """Return a task's comments after validating that the task exists."""
        self.task_repository.get_by_id(task_id)
        return self.repository.list_by_task(
            task_id=task_id,
            limit=limit,
            offset=offset,
        )
