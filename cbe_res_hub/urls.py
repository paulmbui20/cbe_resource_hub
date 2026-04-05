"""cbe_res_hub/urls.py"""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # ── Django admin ────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Authentication (allauth — login, sign-up, password reset, Google OAuth)
    path("accounts/", include("allauth.urls")),

    # ── CMS static pages (/, /pages/<slug>/)
    path("", include("cms.urls")),

    # ── CBC resources (/resources/)
    path("resources/", include("resources.urls")),

    # ── TinyMCE (rich-text editor for CMS admin)
    path("tinymce/", include("tinymce.urls")),

    # ── Silk profiler (dev only — gated below)
    path("silk/", include("silk.urls", namespace="silk")),
]

# ── Development extras ───────────────────────────────────────────────────────
if settings.DEBUG:
    # Serve user-uploaded media files locally
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Django Debug Toolbar
    import debug_toolbar  # noqa: PLC0415
    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
