from rest_framework import serializers

from common.serializers import paginated_serializer

from comments.models import Comment


class CommentCreateSerializer(serializers.Serializer[dict[str, str]]):
    content = serializers.CharField()


class CommentCreateResponseSerializer(serializers.Serializer[dict[str, int]]):
    id = serializers.IntegerField()


class CommentSerializer(serializers.ModelSerializer[Comment]):
    author_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author_id", "content", "created_at"]


class CommentListQuerySerializer(serializers.Serializer[dict[str, object]]):
    limit = serializers.IntegerField(
        min_value=1, max_value=100, required=False, default=20
    )
    offset = serializers.IntegerField(min_value=0, required=False, default=0)


CommentListResponseSerializer = paginated_serializer(CommentSerializer)
