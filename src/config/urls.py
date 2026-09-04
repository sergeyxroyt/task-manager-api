"""URL configuration for the task manager API."""

from django.contrib import admin
from django.urls import include, path
from rest_framework.permissions import AllowAny
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("users.urls")),
    path("api/tasks", include("tasks.urls")),
    path("api/tasks/", include("tasks.urls")),
    path(
        "api/schema",
        SpectacularSwaggerView.as_view(
            url_name="openapi-schema",
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name="swagger-ui",
    ),
    path(
        "api/schema/openapi",
        SpectacularAPIView.as_view(
            authentication_classes=[],
            permission_classes=[AllowAny],
        ),
        name="openapi-schema",
    ),
]
