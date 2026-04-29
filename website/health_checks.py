"""
Optimized health check views for Django application.
"""
import logging
from datetime import datetime, UTC

from django.contrib.auth.decorators import login_not_required
from django.core.cache import cache
from django.db import connections
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

logger = logging.getLogger(__name__)


@never_cache
@require_GET
@login_not_required
def health_check(request):
    """
    Comprehensive health check endpoint.
    Returns 200 if all critical services are healthy, 503 otherwise.
    """
    checks = {
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "healthy",
        "checks": {}
    }

    overall_healthy = True

    # Database checks
    db_healthy = check_databases()
    checks["checks"]["databases"] = db_healthy
    if not db_healthy["healthy"]:
        overall_healthy = False

    # Redis/Cache check
    cache_healthy = check_cache()
    checks["checks"]["cache"] = cache_healthy
    if not cache_healthy["healthy"]:
        overall_healthy = False

    checks["status"] = "healthy" if overall_healthy else "unhealthy"
    status_code = 200 if overall_healthy else 503

    return JsonResponse(checks, status=status_code)


@never_cache
@require_GET
@login_not_required
def liveness_check(request):
    """
    Minimal liveness check - confirms the application is running.
    """
    return JsonResponse({
        "status": "alive",
        "timestamp": datetime.now(UTC).isoformat()
    })


@never_cache
@require_GET
@login_not_required
def readiness_check(request):
    """
    Lightweight readiness check - ensures the application can handle requests.
    Only checks critical services needed to serve traffic.
    """
    checks = {
        "timestamp": datetime.now(UTC).isoformat(),
        "ready": True,
        "checks": {}
    }

    # Quick database check - only default DB
    db_healthy = check_database_quick()
    checks["checks"]["database"] = db_healthy
    if not db_healthy["healthy"]:
        checks["ready"] = False

    # Quick cache check
    cache_healthy = check_cache_quick()
    checks["checks"]["cache"] = cache_healthy
    if not cache_healthy["healthy"]:
        checks["ready"] = False

    status_code = 200 if checks["ready"] else 503
    return JsonResponse(checks, status=status_code)


def check_database_quick():
    """Quick check of only the default database."""
    result = {
        "healthy": True,
        "status": "connected"
    }

    try:
        conn = connections['default']
        # Use a simple query with short timeout
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        result["healthy"] = False
        result["status"] = "error"
        result["error"] = str(e)

    return result


def check_databases():
    """Check all configured database connections."""
    result = {
        "healthy": True,
        "databases": {}
    }

    for db_alias in connections:
        try:
            conn = connections[db_alias]
            # Set a short timeout for health checks
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            result["databases"][db_alias] = {
                "status": "connected",
                "healthy": True
            }
        except Exception as e:
            logger.error(f"Database '{db_alias}' health check failed: {e}")
            result["databases"][db_alias] = {
                "status": "error",
                "healthy": False,
                "error": str(e)
            }
            result["healthy"] = False

    return result


def check_cache_quick():
    """Quick cache connectivity check without read/write test."""
    result = {
        "healthy": True,
        "status": "connected"
    }

    try:
        # Just try to get a non-existent key - this is very fast
        cache.get("_health_check_ping_", version=1)
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        result["healthy"] = False
        result["status"] = "error"
        result["error"] = str(e)

    return result


def check_cache():
    """Full cache connectivity check with read/write test."""
    result = {
        "healthy": True,
        "status": "connected"
    }

    test_key = "health_check_test"
    test_value = datetime.now(UTC).isoformat()

    try:
        # Test write
        cache.set(test_key, test_value, timeout=10)

        # Test read
        retrieved_value = cache.get(test_key)

        if retrieved_value != test_value:
            raise Exception("Cache read/write mismatch")

        # Cleanup
        cache.delete(test_key)

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        result["healthy"] = False
        result["status"] = "error"
        result["error"] = str(e)

    return result


def check_celery():
    """
    Check Celery worker connectivity.
    Note: This is an optional check and may add latency.
    """
    result = {
        "healthy": True,
        "status": "available",
        "workers_count": 0
    }

    try:
        from celery import Celery

        app = Celery('cbe_res_hub')
        app.config_from_object('django.conf:settings', namespace='CELERY')

        # Inspect active workers with short timeout
        inspect = app.control.inspect(timeout=2.0)
        stats = inspect.stats()

        if stats is None or not stats:
            result["healthy"] = False
            result["status"] = "no_workers"
        else:
            result["workers_count"] = len(stats)

    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        result["healthy"] = False
        result["status"] = "error"
        result["error"] = str(e)

    return result


@never_cache
@require_GET
@login_not_required
def celery_health(request):
    """Dedicated endpoint for Celery health check."""
    result = check_celery()
    status_code = 200 if result["healthy"] else 503
    return JsonResponse(result, status=status_code)
