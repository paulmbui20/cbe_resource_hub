"""
ASGI config for cbe_res_hub — Django Channels + Daphne.

Exposes the ASGI callable as a module-level variable named ``application``.
Routes WebSocket connections through Channels; all other requests fall back
to the standard Django ASGI application.

Run with:
    daphne -p 8000 cbe_res_hub.asgi:application
"""
from __future__ import annotations

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbe_res_hub.settings")

# Initialise Django before importing channels routing
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.auth import AuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter(
    {
        # HTTP → standard Django views / HTMX / etc.
        "http": django_asgi_app,

        # WebSocket → AuthMiddlewareStack → URL router
        # Add your WebSocket URL patterns here when needed:
        # "websocket": AuthMiddlewareStack(
        #     URLRouter(websocket_urlpatterns)
        # ),
    }
)
