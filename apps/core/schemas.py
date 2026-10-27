from typing import Any

from ninja import Schema


class ErrorBody(Schema):
    code: str
    message: str
    details: Any = None


class ErrorResponse(Schema):
    """Documents the error envelope in OpenAPI. See ``apps.core.errors``."""

    error: ErrorBody


class HealthResponse(Schema):
    status: str
    database: str
