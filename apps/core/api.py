import logging

from django.db import connection
from django.http import HttpRequest
from ninja import Router

from .schemas import ErrorResponse, HealthResponse

logger = logging.getLogger(__name__)

router = Router(tags=["System"])


@router.get(
    "/health",
    auth=None,
    response={200: HealthResponse, 503: ErrorResponse},
    summary="Service health",
)
def health(request: HttpRequest):
    """Checks the database is reachable. Used by the load balancer and uptime checks (NFR-06)."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        logger.exception("Health check could not reach the database")
        return 503, {
            "error": {
                "code": "service_unavailable",
                "message": "The database is unreachable.",
                "details": None,
            }
        }
    return 200, {"status": "ok", "database": "ok"}
