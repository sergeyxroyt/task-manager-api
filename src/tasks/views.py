from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import OpenApiResponse, extend_schema

from .exceptions import TaskNotFoundError
from .serializers import ErrorSerializer, TaskSerializer
from .services import TaskService


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
