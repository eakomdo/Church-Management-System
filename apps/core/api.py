import logging

from django.db import DatabaseError, connection
from django.http import HttpRequest
from ninja import Router, Status

from .schemas import ErrorResponse, HealthResponse

logger = logging.getLogger(__name__)

router = Router(tags=["System"])


def database_is_reachable() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        logger.exception("Health check could not reach the database")
        return False
    return True


@router.get(
    "/health",
    auth=None,
    response={200: HealthResponse, 503: ErrorResponse},
    summary="Service health",
)
def health(request: HttpRequest):
    """Checks the database is reachable. Used by the load balancer and uptime checks (NFR-06)."""
    if not database_is_reachable():
        return Status(
            503,
            {
                "error": {
                    "code": "service_unavailable",
                    "message": "The database is unreachable.",
                    "details": None,
                }
            },
        )
    return Status(200, {"status": "ok", "database": "ok"})
