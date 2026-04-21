from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def health_check(request):
    checks = {
        "database": _database_ok(),
        "cache": _cache_ok(),
    }
    healthy = all(checks.values())
    return JsonResponse(
        {
            "status": "ok" if healthy else "error",
            "checks": checks,
        },
        status=200 if healthy else 503,
    )


def _database_ok() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def _cache_ok() -> bool:
    try:
        key = "health-check"
        cache.set(key, "ok", 10)
        return cache.get(key) == "ok"
    except Exception:
        return False
