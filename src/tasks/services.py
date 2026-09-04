from .models import Task
from .repositories import TaskRepository


class TaskService:
    def __init__(self, repository: TaskRepository | None = None) -> None:
        self.repository = repository or TaskRepository()

    def get_by_id(self, task_id: int) -> Task:
        return self.repository.get_by_id(task_id)
