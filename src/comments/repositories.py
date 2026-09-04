from common.pagination import PaginatedDTO, build_pagination

from .models import Comment


class CommentRepository:
    def list_by_task(
        self, *, task_id: int, limit: int, offset: int
    ) -> PaginatedDTO[Comment]:
        queryset = Comment.objects.filter(task_id=task_id)
        total = queryset.count()
        return PaginatedDTO(
            data=list(queryset[offset : offset + limit]),
            pagination=build_pagination(limit=limit, offset=offset, total=total),
        )
