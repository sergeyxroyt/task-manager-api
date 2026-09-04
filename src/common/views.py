from typing import Any

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.views import APIView


class QueryParamsAPIView(APIView):
    """Base view that validates query parameters with a serializer."""

    query_serializer_class: type[serializers.Serializer[Any]]

    def get_query_params(self, request: Request) -> dict[str, Any]:
        """Return validated query parameters or raise a validation error."""
        serializer = self.query_serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)


class BodyAPIView(APIView):
    """Base view that validates request bodies with a serializer."""

    body_serializer_class: type[serializers.Serializer[Any]]

    def get_body(self, request: Request) -> dict[str, Any]:
        """Return validated request data or raise a validation error."""
        serializer = self.body_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)
