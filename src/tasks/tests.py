from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from typing import ClassVar
from unittest.mock import Mock, patch

from common.pagination import PaginatedDTO, PaginationDTO

from .exceptions import TaskNotFoundError
from .models import Task
from .repositories import TaskRepository
from .services import TaskService
from .views import TaskListView
from users.models import User


class TaskRepositoryTests(SimpleTestCase):
    @patch("tasks.repositories.Task.objects.all")
    def test_list_applies_statuses_and_pagination(self, get_tasks: Mock) -> None:
        queryset = get_tasks.return_value
        filtered_queryset = queryset.filter.return_value
        filtered_queryset.count.return_value = 21
        filtered_queryset.__getitem__.return_value = [Task(id=42, title="Task")]

        result = TaskRepository().list(limit=10, offset=20, statuses=["todo", "done"])

        self.assertEqual(result.data, [Task(id=42, title="Task")])
        self.assertEqual(result.pagination.total, 21)
        self.assertEqual(result.pagination.page, 3)
        self.assertEqual(result.pagination.total_pages, 3)
        queryset.filter.assert_called_once_with(status__in=["todo", "done"])
        filtered_queryset.__getitem__.assert_called_once_with(slice(20, 30))

    @patch("tasks.repositories.Task.objects.all")
    def test_list_without_statuses_uses_all_tasks(self, get_tasks: Mock) -> None:
        queryset = get_tasks.return_value
        queryset.count.return_value = 0
        queryset.__getitem__.return_value = []

        result = TaskRepository().list(limit=10, offset=20)

        self.assertEqual(result.data, [])
        self.assertEqual(result.pagination.total, 0)
        self.assertEqual(result.pagination.total_pages, 0)
        queryset.filter.assert_not_called()
        queryset.__getitem__.assert_called_once_with(slice(20, 30))

    @patch("tasks.repositories.Task.objects.get")
    def test_get_by_id_returns_task(self, get_task: Mock) -> None:
        task = Task(id=42, title="Prepare report")
        get_task.return_value = task

        result = TaskRepository().get_by_id(42)

        self.assertIs(result, task)
        get_task.assert_called_once_with(pk=42)

    @patch("tasks.repositories.Task.objects.get")
    def test_get_by_id_raises_task_not_found_error_for_missing_task(
        self, get_task: Mock
    ) -> None:
        get_task.side_effect = Task.DoesNotExist

        with self.assertRaises(TaskNotFoundError) as context:
            TaskRepository().get_by_id(42)

        self.assertIsInstance(context.exception.__cause__, Task.DoesNotExist)
        get_task.assert_called_once_with(pk=42)

    @patch("tasks.repositories.Task.objects.get")
    def test_get_by_id_propagates_unexpected_repository_error(
        self, get_task: Mock
    ) -> None:
        error = RuntimeError("database is unavailable")
        get_task.side_effect = error

        with self.assertRaisesRegex(RuntimeError, "database is unavailable"):
            TaskRepository().get_by_id(42)

        get_task.assert_called_once_with(pk=42)


class TaskServiceTests(SimpleTestCase):
    @patch("tasks.services.TaskRepository")
    def test_list_returns_tasks_from_repository(self, repository_class: Mock) -> None:
        repository = repository_class.return_value
        expected = PaginatedDTO(
            data=[Task(id=42, title="Task")],
            pagination=PaginationDTO(page=3, per_page=10, total=21, total_pages=3),
        )
        repository.list.return_value = expected
        service = TaskService()

        result = service.list(limit=10, offset=20, statuses=["todo"])

        self.assertIs(result, expected)
        repository.list.assert_called_once_with(limit=10, offset=20, statuses=["todo"])

    @patch("tasks.services.TaskRepository")
    def test_get_by_id_returns_task_from_repository(
        self, repository_class: Mock
    ) -> None:
        task = Task(id=42, title="Prepare report")
        repository = repository_class.return_value
        repository.get_by_id.return_value = task
        service = TaskService()

        result = service.get_by_id(42)

        self.assertIs(result, task)
        repository.get_by_id.assert_called_once_with(42)

    @patch("tasks.services.TaskRepository")
    def test_get_by_id_propagates_task_not_found_error(
        self, repository_class: Mock
    ) -> None:
        repository = repository_class.return_value
        repository.get_by_id.side_effect = TaskNotFoundError
        service = TaskService()

        with self.assertRaises(TaskNotFoundError):
            service.get_by_id(42)

        repository.get_by_id.assert_called_once_with(42)

    @patch("tasks.services.TaskRepository")
    def test_get_by_id_propagates_unexpected_repository_error(
        self, repository_class: Mock
    ) -> None:
        repository = repository_class.return_value
        repository.get_by_id.side_effect = RuntimeError("database is unavailable")
        service = TaskService()

        with self.assertRaisesRegex(RuntimeError, "database is unavailable"):
            service.get_by_id(42)

        repository.get_by_id.assert_called_once_with(42)


class TaskDetailApiTests(TestCase):
    user: ClassVar[User]
    task: ClassVar[Task]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            username="task-user", password="test-password"
        )
        cls.task = Task.objects.create(
            title="Prepare report",
            description="Prepare the monthly report.",
            status="in_progress",
            creator=cls.user,
        )

    def setUp(self) -> None:
        self.client: APIClient = APIClient()
        self.url = f"/api/tasks/{self.task.pk}"

    def test_authenticated_user_can_get_task(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["id"], self.task.pk)
        self.assertEqual(response.json()["title"], self.task.title)
        self.assertEqual(response.json()["creator_id"], self.user.pk)
        self.assertIsNone(response.json()["assignee_id"])
        self.assertNotIn("creator", response.json())
        self.assertNotIn("assignee", response.json())

    def test_missing_task_returns_404(self) -> None:
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/tasks/999999")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Task not found.")

    def test_unauthenticated_user_returns_401(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TaskListIntegrationTests(TestCase):
    user: ClassVar[User]
    assignee: ClassVar[User]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            username="list-user", password="test-password"
        )
        cls.assignee = get_user_model().objects.create_user(
            username="list-assignee", password="test-password"
        )
        for task_status, title in (
            ("todo", "First task"),
            ("in_progress", "Second task"),
            ("done", "Third task"),
            ("todo", "Fourth task"),
        ):
            Task.objects.create(
                title=title,
                status=task_status,
                creator=cls.user,
                assignee=cls.assignee,
            )

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/tasks"

    def test_list_supports_limit_and_offset(self) -> None:
        response = self.client.get(self.url, {"limit": 2, "offset": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [task["title"] for task in response.json()["data"]],
            ["Third task", "Second task"],
        )
        self.assertEqual(
            response.json()["pagination"],
            {
                "page": 1,
                "per_page": 2,
                "total": 4,
                "total_pages": 2,
            },
        )

    def test_list_paginates_without_skipping_or_repeating_tasks(self) -> None:
        first_page = self.client.get(self.url, {"limit": 2, "offset": 0})
        second_page = self.client.get(self.url, {"limit": 2, "offset": 2})

        self.assertEqual(first_page.status_code, status.HTTP_200_OK)
        self.assertEqual(second_page.status_code, status.HTTP_200_OK)

        first_data = first_page.json()
        second_data = second_page.json()
        first_ids = [task["id"] for task in first_data["data"]]
        second_ids = [task["id"] for task in second_data["data"]]

        self.assertEqual(len(first_ids), 2)
        self.assertEqual(len(second_ids), 2)
        self.assertTrue(set(first_ids).isdisjoint(second_ids))
        self.assertEqual(
            first_ids + second_ids,
            list(Task.objects.values_list("id", flat=True).order_by("-created_at")),
        )
        self.assertEqual(
            first_data["pagination"],
            {"page": 1, "per_page": 2, "total": 4, "total_pages": 2},
        )
        self.assertEqual(
            second_data["pagination"],
            {"page": 2, "per_page": 2, "total": 4, "total_pages": 2},
        )

    def test_list_filters_by_multiple_statuses(self) -> None:
        response = self.client.get(
            self.url,
            [("status", "todo"), ("status", "done")],
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            {task["status"] for task in response.json()["data"]}, {"todo", "done"}
        )
        self.assertEqual(len(response.json()["data"]), 3)

    def test_list_rejects_unknown_status(self) -> None:
        response = self.client.get(self.url, {"status": "missing"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_does_not_query_users_for_foreign_key_ids(self) -> None:
        with self.assertNumQueries(2):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TaskListApiTests(TestCase):
    def setUp(self) -> None:
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            username="api-list-user", password="test-password"
        )

    @patch("tasks.views.TaskService")
    def test_get_delegates_validated_query_to_service(
        self, service_class: Mock
    ) -> None:
        service = service_class.return_value
        service.list.return_value = PaginatedDTO(
            data=[],
            pagination=PaginationDTO(page=3, per_page=5, total=12, total_pages=3),
        )
        request = self.factory.get(
            "/api/tasks?limit=5&offset=10&status=todo,in_progress"
        )
        force_authenticate(request, user=self.user)

        response = TaskListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service.list.assert_called_once_with(
            limit=5, offset=10, statuses=["todo", "in_progress"]
        )

    def test_get_rejects_invalid_pagination_parameters(self) -> None:
        request = self.factory.get("/api/tasks?limit=0&offset=-1")
        force_authenticate(request, user=self.user)

        response = TaskListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_user_returns_401(self) -> None:
        request = self.factory.get("/api/tasks")

        response = TaskListView.as_view()(request)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
