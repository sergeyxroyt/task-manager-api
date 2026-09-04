from typing import Any

from rest_framework import serializers
from rest_framework.request import Request
from rest_framework.views import APIView


class QueryParamsAPIView(APIView):
    query_serializer_class: type[serializers.Serializer[Any]]

    def get_query_params(self, request: Request) -> dict[str, Any]:
        serializer = self.query_serializer_class(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)


class BodyAPIView(APIView):
    body_serializer_class: type[serializers.Serializer[Any]]

    def get_body(self, request: Request) -> dict[str, Any]:
        serializer = self.body_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return dict(serializer.validated_data)
