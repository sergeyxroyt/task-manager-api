from typing import Any

from rest_framework import serializers

from common.serializers import paginated_serializer

from .models import Task


class TaskSerializer(serializers.ModelSerializer[Task]):
    creator_id = serializers.IntegerField(read_only=True)
    assignee_id = serializers.IntegerField(read_only=True)

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


class TaskCreateSerializer(serializers.Serializer[dict[str, object]]):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    assignee_id = serializers.IntegerField(required=False, allow_null=True, min_value=1)


class TaskCreateResponseSerializer(serializers.Serializer[dict[str, int]]):
    id = serializers.IntegerField()


class ErrorSerializer(serializers.Serializer[dict[str, str]]):
    detail = serializers.CharField()


class TaskListQuerySerializer(serializers.Serializer[dict[str, object]]):
    limit = serializers.IntegerField(
        min_value=1, max_value=100, required=False, default=20
    )
    offset = serializers.IntegerField(min_value=0, required=False, default=0)
    statuses = serializers.ListField(
        child=serializers.ChoiceField(choices=Task.Status.choices),
        required=False,
        default=list,
    )

    def to_internal_value(self, data: Any) -> dict[str, object]:
        if hasattr(data, "getlist"):
            query_params = data.copy()
            raw_statuses = query_params.getlist("status")
            raw_statuses.extend(query_params.getlist("statuses"))
            statuses = [
                status_value.strip()
                for value in raw_statuses
                for status_value in value.split(",")
                if status_value.strip()
            ]
            query_params.setlist("statuses", statuses)
            data = query_params

        return dict(super().to_internal_value(data))


TaskListResponseSerializer = paginated_serializer(TaskSerializer)
