"""cbe_res_hub/urls.py"""
from __future__ import annotations

import sys

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # ── Root ────────────────────────────────────────────────────────────────
    path("", include("website.urls.website_urls")),

    # ── Django admin ─────────────────────────────────────────────────────────
    path("admin/", admin.site.urls),

    # ── Authentication (allauth — login, sign-up, password, Google OAuth) ────
    path("accounts/", include("allauth.urls")),

    # ── Account dashboard / profile ──────────────────────────────────────────
    path("account/", include("accounts.urls", namespace="accounts")),
    path("management/", include("website.urls.admin_urls", namespace="management")),

    # ── CBC resources (/resources/) ──────────────────────────────────────────
    path("resources/", include("resources.urls")),

    # ── CMS pages (/pages/<slug>/) ───────────────────────────────────────────
    path("pages/", include("cms.urls")),

    # ── TinyMCE ──────────────────────────────────────────────────────────────
    path("tinymce/", include("tinymce.urls")),

]

# ── Development only (excludes testing environment)─────────────────────────────
if not ("pytest" in sys.modules or "test" in sys.argv) or settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    import debug_toolbar  # noqa: PLC0415

    urlpatterns += [
        # ── Django Debug Toolbar ───────────────────────────────────────────────
        path("__debug__/", include(debug_toolbar.urls)),
        # ── Silk profiler ──────────────────────────────────────────────────────
        path("silk/", include("silk.urls", namespace="silk")),

    ]
