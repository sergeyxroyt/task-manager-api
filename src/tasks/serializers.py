from rest_framework import serializers
from django.contrib.auth import get_user_model

from .models import Task


class TaskSerializer(serializers.ModelSerializer[Task]):
    creator_id = serializers.PrimaryKeyRelatedField(
        source="creator", queryset=get_user_model().objects.all()
    )
    assignee_id = serializers.PrimaryKeyRelatedField(
        source="assignee",
        queryset=get_user_model().objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Task
        fields = [
            "id",
            "title",
            "description",
            "status",
            "creator_id",
            "assignee_id",
            "created_at",
            "updated_at",
        ]


class ErrorSerializer(serializers.Serializer[dict[str, str]]):
    detail = serializers.CharField()
