"""
ASGI config for cbe_res_hub.

Exposes the ASGI callable as a module-level variable named ``application``.

"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cbe_res_hub.settings")

application = get_asgi_application()
