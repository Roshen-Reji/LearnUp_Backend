"""
LearnUp Backend — URL Configuration
=====================================
Root URL router. All API endpoints are versioned under /api/v1/.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from core.views import HealthCheckView, FileUploadView

urlpatterns = [
    # ─── Admin Panel ─────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ─── Health Check (Load balancers, monitoring) ───────────
    path("api/health/", HealthCheckView.as_view(), name="health-check"),

    # ─── Upload (Generic) ───────────────────────────────────
    path("api/v1/upload/", FileUploadView.as_view(), name="upload"),

    # ─── API v1 ──────────────────────────────────────────────
    path("api/v1/auth/", include("apps.accounts.urls.auth_urls")),
    path("api/v1/users/", include("apps.accounts.urls.user_urls")),
    path("api/v1/aptitude/", include("apps.aptitude.urls")),
    path("api/v1/community/", include("apps.community.urls")),
    path("api/v1/notes/", include("apps.notes.urls")),
    path("api/v1/roadmaps/", include("apps.roadmaps.urls")),
    path("api/v1/placements/", include("apps.placements.urls")),
    path("api/v1/github/", include("apps.github.urls")),
    path("api/v1/ai/", include("apps.ai.urls")),
    path("api/v1/quotes/", include("apps.quotes.urls")),

    # ─── API Documentation ──────────────────────────────────
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
