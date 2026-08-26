from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from .health import api_root, database_health, health

urlpatterns = [
    path("", health, name="health"),
    path("health/", health, name="health-detail"),
    path("api/", api_root, name="api-root"),
    path("api/health/", database_health, name="api-health"),
    path("django-admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/students/", include("students.urls")),
    path("api/civilian/", include("civilian.urls")),
    path("api/citizens/", include("citizens.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
