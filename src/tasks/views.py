from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

from common.views import QueryParamsAPIView

from .exceptions import TaskNotFoundError
from .serializers import (
    ErrorSerializer,
    TaskListQuerySerializer,
    TaskListResponseSerializer,
    TaskSerializer,
)
from .services import TaskService


class TaskListView(QueryParamsAPIView):
    permission_classes = [IsAuthenticated]
    query_serializer_class = TaskListQuerySerializer

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
