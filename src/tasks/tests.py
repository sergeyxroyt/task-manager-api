from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from typing import ClassVar

from .models import Task
from users.models import User


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
