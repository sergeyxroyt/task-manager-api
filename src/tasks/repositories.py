from .exceptions import TaskNotFoundError
from .models import Task


class TaskRepository:
    def get_by_id(self, task_id: int) -> Task:
        try:
            return Task.objects.get(pk=task_id)
        except Task.DoesNotExist as exc:
            raise TaskNotFoundError from exc
