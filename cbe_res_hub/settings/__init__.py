"""
cbe_res_hub/settings/__init__.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Auto-selects the correct settings module so that existing code that sets

    DJANGO_SETTINGS_MODULE=cbe_res_hub.settings

The selection order is:

  1. pytest / manage.py test  → testing.py
  2. ENVIRONMENT=production   → production.py
  3. everything else          → development.py

"""

import os
import sys

# ── Detect test runs before importing anything else ──────────────────────────
_testing = (
        "pytest" in sys.modules
        or "pytest" in sys.argv[0]
        or "test" in sys.argv
)

_environment = os.getenv("ENVIRONMENT")

if _testing or _environment == "testing":
    from .testing import *  # noqa: F401, F403
elif _environment == "production":
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
