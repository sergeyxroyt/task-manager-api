from typing import cast

from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

from common.views import BodyAPIView, QueryParamsAPIView
from tasks.exceptions import TaskNotFoundError
from tasks.serializers import ErrorSerializer
from users.models import User

from .serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
    CommentListQuerySerializer,
    CommentListResponseSerializer,
)
from .services import CommentService


class CommentListView(QueryParamsAPIView, BodyAPIView):
    permission_classes = [IsAuthenticated]
    query_serializer_class = CommentListQuerySerializer
    body_serializer_class = CommentCreateSerializer

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.service = CommentService()

    @extend_schema(
        tags=["comments"],
        parameters=[CommentListQuerySerializer],
        responses={
            200: CommentListResponseSerializer,
            400: OpenApiResponse(
                response=ErrorSerializer,
                description="Invalid query",
            ),
            401: OpenApiResponse(
                response=ErrorSerializer,
                description="Unauthorized",
            ),
            404: OpenApiResponse(
                response=ErrorSerializer,
                description="Task not found",
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

    @extend_schema(
        tags=["comments"],
        request=CommentCreateSerializer,
        responses={
            201: CommentCreateResponseSerializer,
            400: OpenApiResponse(
                response=ErrorSerializer,
                description="Invalid body",
            ),
            401: OpenApiResponse(
                response=ErrorSerializer,
                description="Unauthorized",
            ),
            404: OpenApiResponse(
                response=ErrorSerializer,
                description="Task not found",
            ),
        },
    )
    def post(self, request: Request, task_id: int) -> Response:
        body = self.get_body(request)

        try:
            comment = self.service.create(
                task_id=task_id,
                author=cast(User, request.user),
                content=body["content"],
            )
        except TaskNotFoundError:
            raise NotFound("Task not found.")

        return Response(
            CommentCreateResponseSerializer({"id": comment.pk}).data,
            status=status.HTTP_201_CREATED,
        )
