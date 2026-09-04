from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from common.views import QueryParamsAPIView
from tasks.exceptions import TaskNotFoundError
from tasks.serializers import ErrorSerializer

from .serializers import (
    CommentListQuerySerializer,
    CommentListResponseSerializer,
)
from .services import CommentService


class CommentListView(QueryParamsAPIView):
    permission_classes = [IsAuthenticated]
    query_serializer_class = CommentListQuerySerializer

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.service = CommentService()

    @extend_schema(
        parameters=[CommentListQuerySerializer],
        responses={
            200: CommentListResponseSerializer,
            400: OpenApiResponse(response=ErrorSerializer, description="Invalid query"),
            401: OpenApiResponse(response=ErrorSerializer, description="Unauthorized"),
            404: OpenApiResponse(
                response=ErrorSerializer, description="Task not found"
            ),
        },
    )
    def get(self, request: Request, task_id: int) -> Response:
        query = self.get_query_params(request)

        try:
            comments = self.service.list_by_task(
                task_id=task_id,
                limit=query["limit"],
                offset=query["offset"],
            )
        except TaskNotFoundError:
            raise NotFound("Task not found.")

        return Response(
            CommentListResponseSerializer(
                {"data": comments.data, "pagination": comments.pagination}
            ).data,
            status=status.HTTP_200_OK,
        )
