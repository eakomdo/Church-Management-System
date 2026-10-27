"""One error envelope for every API failure.

Every non-2xx response has the shape::

    {"error": {"code": "not_found", "message": "Member not found.", "details": null}}

Clients branch on ``code``; ``message`` is safe to show to users.
"""

import logging
from typing import Any

from django.conf import settings
from django.core.exceptions import NON_FIELD_ERRORS
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404, HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.errors import ValidationError as NinjaValidationError

logger = logging.getLogger(__name__)

STATUS_CODES = {
    400: "bad_request",
    401: "not_authenticated",
    403: "permission_denied",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "validation_error",
    429: "throttled",
    500: "server_error",
    503: "service_unavailable",
}


class APIError(Exception):
    """Raise from services or endpoints to return a specific error to the client."""

    status_code = 400
    code = "bad_request"
    message = "The request could not be processed."

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        details: Any = None,
    ) -> None:
        self.message = message or self.message
        self.code = code or self.code
        self.details = details
        super().__init__(self.message)


class NotFound(APIError):
    status_code = 404
    code = "not_found"
    message = "The requested resource was not found."


class Forbidden(APIError):
    status_code = 403
    code = "permission_denied"
    message = "You do not have permission to perform this action."


class Conflict(APIError):
    status_code = 409
    code = "conflict"
    message = "The request conflicts with the current state of the resource."


def error_response(
    api: NinjaAPI,
    request: HttpRequest,
    *,
    status: int,
    code: str,
    message: str,
    details: Any = None,
) -> HttpResponse:
    body = {"error": {"code": code, "message": message, "details": details}}
    return api.create_response(request, body, status=status)


def validation_details(exc: DjangoValidationError) -> list[dict[str, Any]]:
    """Reshape a Django ValidationError like Ninja's request errors: ``[{loc, msg, type}]``."""
    error_dict = getattr(exc, "error_dict", None)
    if error_dict is not None:
        by_field = error_dict.items()
    else:
        by_field = [(NON_FIELD_ERRORS, exc.error_list or [])]
    return [
        {
            "loc": [] if field == NON_FIELD_ERRORS else [field],
            "msg": message,
            "type": error.code or "invalid",
        }
        for field, errors in by_field
        for error in errors
        for message in error.messages
    ]


def register_exception_handlers(api: NinjaAPI) -> None:
    @api.exception_handler(APIError)
    def handle_api_error(request: HttpRequest, exc: APIError) -> HttpResponse:
        return error_response(
            api,
            request,
            status=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )

    @api.exception_handler(NinjaValidationError)
    def handle_validation_error(request: HttpRequest, exc: NinjaValidationError) -> HttpResponse:
        return error_response(
            api,
            request,
            status=422,
            code="validation_error",
            message="Some fields are missing or invalid.",
            details=exc.errors,
        )

    @api.exception_handler(DjangoValidationError)
    def handle_django_validation_error(
        request: HttpRequest, exc: DjangoValidationError
    ) -> HttpResponse:
        # Raised by services and model validation, e.g. "this phone number is already in use".
        return error_response(
            api,
            request,
            status=422,
            code="validation_error",
            message="Some fields are missing or invalid.",
            details=validation_details(exc),
        )

    @api.exception_handler(HttpError)
    def handle_http_error(request: HttpRequest, exc: HttpError) -> HttpResponse:
        return error_response(
            api,
            request,
            status=exc.status_code,
            code=STATUS_CODES.get(exc.status_code, "error"),
            message=str(exc),
        )

    @api.exception_handler(Http404)
    def handle_404(request: HttpRequest, exc: Http404) -> HttpResponse:
        return error_response(api, request, status=404, code="not_found", message=NotFound.message)

    @api.exception_handler(DjangoPermissionDenied)
    def handle_permission_denied(request: HttpRequest, exc: DjangoPermissionDenied) -> HttpResponse:
        return error_response(
            api, request, status=403, code="permission_denied", message=Forbidden.message
        )

    @api.exception_handler(Exception)
    def handle_unexpected(request: HttpRequest, exc: Exception) -> HttpResponse:
        if settings.DEBUG:
            raise exc
        # Log the traceback for us, but never leak internals to the client.
        logger.exception("Unhandled API error on %s %s", request.method, request.path)
        return error_response(
            api,
            request,
            status=500,
            code="server_error",
            message="Something went wrong on our side. Please try again.",
        )
