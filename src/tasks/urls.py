from django.urls import path

from comments.views import CommentListView

from .views import TaskDetailView, TaskListView


urlpatterns = [
    path("", TaskListView.as_view(), name="task-list"),
    path("<int:task_id>/comments/", CommentListView.as_view(), name="comment-list"),
    path("<int:task_id>/", TaskDetailView.as_view(), name="task-detail"),
]
