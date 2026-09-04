from typing import cast

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

from common.views import BodyAPIView, QueryParamsAPIView
from users.models import User

from .exceptions import AssigneeNotFoundError, TaskNotFoundError
from .serializers import (
    ErrorSerializer,
    TaskCreateResponseSerializer,
    TaskCreateSerializer,
    TaskListQuerySerializer,
    TaskListResponseSerializer,
    TaskSerializer,
)
from .services import TaskService


class TaskListView(QueryParamsAPIView, BodyAPIView):
    permission_classes = [IsAuthenticated]
    query_serializer_class = TaskListQuerySerializer
    body_serializer_class = TaskCreateSerializer

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.service = TaskService()

    @extend_schema(
        parameters=[TaskListQuerySerializer],
        responses={
            200: TaskListResponseSerializer,
            400: OpenApiResponse(response=ErrorSerializer, description="Invalid query"),
            401: OpenApiResponse(response=ErrorSerializer, description="Unauthorized"),
        },
    )
    def get(self, request: Request) -> Response:
        query = self.get_query_params(request)

        tasks = self.service.list(
            limit=query["limit"],
            offset=query["offset"],
            statuses=query["statuses"],
        )
        return Response(
            TaskListResponseSerializer(
                {"data": tasks.data, "pagination": tasks.pagination}
            ).data,
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        request=TaskCreateSerializer,
        responses={
            201: TaskCreateResponseSerializer,
            400: OpenApiResponse(response=ErrorSerializer, description="Invalid body"),
            401: OpenApiResponse(response=ErrorSerializer, description="Unauthorized"),
            404: OpenApiResponse(
                response=ErrorSerializer, description="Assignee not found"
            ),
        },
    )
    def post(self, request: Request) -> Response:
        body = self.get_body(request)
        user = cast(User, request.user)

        try:
            task = self.service.create(
                title=body["title"],
                description=body["description"],
                assignee_id=body.get("assignee_id"),
                user=user,
            )
        except AssigneeNotFoundError:
            raise NotFound("Assignee not found.")

        return Response(
            TaskCreateResponseSerializer({"id": task.pk}).data,
            status=status.HTTP_201_CREATED,
        )


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.service = TaskService()

    @extend_schema(
        responses={
            200: TaskSerializer,
            401: OpenApiResponse(response=ErrorSerializer, description="Unauthorized"),
            404: OpenApiResponse(response=ErrorSerializer, description="Not found"),
        }
    )
    def get(self, request: Request, task_id: int) -> Response:
        try:
            task = self.service.get_by_id(task_id)
        except TaskNotFoundError:
            raise NotFound("Task not found.")

        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)
