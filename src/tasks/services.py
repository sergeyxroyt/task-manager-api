from collections.abc import Sequence
from typing import cast

from common.pagination import PaginatedDTO
from users.models import User
from users.repositories import UserRepository

from .exceptions import AssigneeNotFoundError
from .models import Task
from .repositories import TaskRepository


class TaskService:
    def __init__(
        self,
        repository: TaskRepository | None = None,
        user_repository: UserRepository | None = None,
    ) -> None:
        self.repository = repository or TaskRepository()
        self.user_repository = user_repository or UserRepository()

    def create(
        self,
        *,
        title: str,
        description: str,
        user: User,
        assignee_id: int | None = None,
    ) -> Task:
        if assignee_id is not None and not self.user_repository.is_exists(
            assignee_id
        ):
            raise AssigneeNotFoundError

        return self.repository.create(
            title=title,
            description=description,
            creator=user,
            assignee_id=assignee_id,
        )

    def list(
        self,
        *,
        limit: int,
        offset: int,
        statuses: Sequence[str] = (),
    ) -> PaginatedDTO[Task]:
        return self.repository.list(
            limit=limit,
            offset=offset,
            statuses=statuses,
        )

    def get_by_id(self, task_id: int) -> Task:
        return self.repository.get_by_id(task_id)

    def update(self, *, task_id: int, **fields: str | int | None) -> None:
        task = self.repository.get_by_id(task_id)

        assignee_id = fields.get("assignee_id")
        if assignee_id is not None and not self.user_repository.is_exists(
            cast(int, assignee_id)
        ):
            raise AssigneeNotFoundError

        self.repository.update(task=task, **fields)

    def delete(self, *, task_id: int) -> None:
        task = self.repository.get_by_id(task_id)
        self.repository.delete(task=task)
