from typing import ClassVar
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory

from common.pagination import PaginatedDTO, PaginationDTO
from tasks.exceptions import TaskNotFoundError
from tasks.models import Task
from users.models import User
from users.tests import DefaultTestUser

from comments.models import Comment
from comments.repositories import CommentRepository
from comments.services import CommentService
from comments.views import CommentListView


class DefaultTestComment:
    id: ClassVar[int] = 2
    content: ClassVar[str] = "Comment"


class CommentRepositoryTests(SimpleTestCase):
    @patch("comments.repositories.Comment.objects.create")
    def test_create_returns_created_comment(
        self,
        create_comment: Mock,
    ) -> None:
        comment = Comment(
            id=DefaultTestComment.id,
            content=DefaultTestComment.content,
        )
        create_comment.return_value = comment
        author = User(id=DefaultTestUser.id, username=DefaultTestUser.username)

        result = CommentRepository().create(
            task_id=42,
            author=author,
            content=DefaultTestComment.content,
        )

        self.assertIs(result, comment)
        create_comment.assert_called_once_with(
            task_id=42,
            author=author,
            content=DefaultTestComment.content,
        )

    @patch("comments.repositories.Comment.objects.filter")
    def test_list_by_task_returns_paginated_comments(
        self, filter_comments: Mock
    ) -> None:
        queryset = filter_comments.return_value
        queryset.count.return_value = 3
        queryset.__getitem__.return_value = [
            Comment(
                id=DefaultTestComment.id,
                content=DefaultTestComment.content,
            ),
        ]

        result = CommentRepository().list_by_task(
            task_id=42,
            limit=1,
            offset=1,
        )

        self.assertEqual(
            result.data,
            [
                Comment(
                    id=DefaultTestComment.id,
                    content=DefaultTestComment.content,
                )
            ],
        )
        self.assertEqual(
            result.pagination,
            PaginationDTO(page=2, per_page=1, total=3, total_pages=3),
        )
        filter_comments.assert_called_once_with(task_id=42)
        queryset.__getitem__.assert_called_once_with(slice(1, 2))


class CommentServiceTests(SimpleTestCase):
    @patch("comments.services.TaskRepository")
    @patch("comments.services.CommentRepository")
    def test_create_checks_task_and_creates_comment(
        self, repository_class: Mock, task_repository_class: Mock
    ) -> None:
        comment = Comment(
            id=DefaultTestComment.id,
            content=DefaultTestComment.content,
        )
        repository_class.return_value.create.return_value = comment
        author = User(id=DefaultTestUser.id, username=DefaultTestUser.username)

        result = CommentService().create(
            task_id=42,
            author=author,
            content=DefaultTestComment.content,
        )

        self.assertIs(result, comment)
        task_repository_class.return_value.get_by_id.assert_called_once_with(
            42
        )
        repository_class.return_value.create.assert_called_once_with(
            task_id=42,
            author=author,
            content=DefaultTestComment.content,
        )

    @patch("comments.services.TaskRepository")
    @patch("comments.services.CommentRepository")
    def test_create_does_not_create_comment_for_missing_task(
        self, repository_class: Mock, task_repository_class: Mock
    ) -> None:
        task_repository_class.return_value.get_by_id.side_effect = (
            TaskNotFoundError
        )

        with self.assertRaises(TaskNotFoundError):
            CommentService().create(
                task_id=42,
                author=User(id=DefaultTestUser.id),
                content=DefaultTestComment.content,
            )

        repository_class.return_value.create.assert_not_called()

    @patch("comments.services.TaskRepository")
    @patch("comments.services.CommentRepository")
    def test_list_by_task_checks_task_and_returns_comments(
        self, repository_class: Mock, task_repository_class: Mock
    ) -> None:
        expected = PaginatedDTO(
            data=[
                Comment(
                    id=DefaultTestComment.id,
                    content=DefaultTestComment.content,
                )
            ],
            pagination=PaginationDTO(
                page=1,
                per_page=20,
                total=1,
                total_pages=1,
            ),
        )
        repository_class.return_value.list_by_task.return_value = expected

        result = CommentService().list_by_task(task_id=42, limit=20, offset=0)

        self.assertIs(result, expected)
        task_repository_class.return_value.get_by_id.assert_called_once_with(
            42
        )
        repository_class.return_value.list_by_task.assert_called_once_with(
            task_id=42, limit=20, offset=0
        )

    @patch("comments.services.TaskRepository")
    @patch("comments.services.CommentRepository")
    def test_list_by_task_does_not_query_comments_for_missing_task(
        self, repository_class: Mock, task_repository_class: Mock
    ) -> None:
        task_repository_class.return_value.get_by_id.side_effect = (
            TaskNotFoundError
        )

        with self.assertRaises(TaskNotFoundError):
            CommentService().list_by_task(task_id=42, limit=20, offset=0)

        repository_class.return_value.list_by_task.assert_not_called()


class CommentListIntegrationTests(TestCase):
    url_template: ClassVar[str] = "/api/tasks/{task_id}/comments/"
    user: ClassVar[AbstractBaseUser]
    task: ClassVar[Task]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = get_user_model().objects.create_user(
            username="comment-user", password=DefaultTestUser.password
        )
        cls.task = Task.objects.create(title="Task", creator=cls.user)
        for content in ("First comment", "Second comment", "Third comment"):
            Comment.objects.create(
                task=cls.task,
                author=cls.user,
                content=content,
            )

    def setUp(self) -> None:
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = self.url_template.format(task_id=self.task.pk)

    def test_missing_task_returns_404(self) -> None:
        response = self.client.get(self.url_template.format(task_id=999999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Task not found.")

    def test_list_returns_paginated_comments(self) -> None:
        response = self.client.get(self.url, {"limit": 2, "offset": 1})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [comment["content"] for comment in response.json()["data"]],
            ["Second comment", "First comment"],
        )
        self.assertEqual(
            response.json()["pagination"],
            {"page": 1, "per_page": 2, "total": 3, "total_pages": 2},
        )

    def test_create_returns_comment_id(self) -> None:
        response = self.client.post(
            self.url,
            {"content": "New comment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        comment_id = response.json()["id"]
        self.assertTrue(Comment.objects.filter(pk=comment_id).exists())
        comment = Comment.objects.get(pk=comment_id)
        self.assertEqual(comment.task_id, self.task.pk)
        self.assertEqual(comment.author_id, self.user.pk)
        self.assertEqual(comment.content, "New comment")

    def test_create_for_missing_task_returns_404(self) -> None:
        response = self.client.post(
            self.url_template.format(task_id=999999),
            {"content": "New comment"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()["detail"], "Task not found.")


class CommentListApiTests(TestCase):
    url = "/api/tasks/42/comments/"

    def setUp(self) -> None:
        self.factory = APIRequestFactory()

    def test_unauthenticated_user_returns_401(self) -> None:
        request = self.factory.get(self.url)

        response = CommentListView.as_view()(request, task_id=42)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_user_cannot_create_comment(self) -> None:
        request = self.factory.post(
            self.url,
            {"content": "Comment"},
            format="json",
        )

        response = CommentListView.as_view()(request, task_id=42)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
