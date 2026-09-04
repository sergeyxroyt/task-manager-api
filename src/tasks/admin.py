from django.contrib import admin

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    list_display = ("title", "status", "creator", "assignee", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "description")
