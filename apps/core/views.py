from django.http import HttpRequest, HttpResponse, JsonResponse
from django.views import defaults

# Requests that fail before reaching Ninja (an unknown /api/ URL, or a crash in middleware)
# still get the API error envelope instead of an HTML page.


def _is_api_request(request: HttpRequest) -> bool:
    return request.path.startswith("/api/")


def _error(status: int, code: str, message: str) -> JsonResponse:
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": None}}, status=status
    )


def not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    if _is_api_request(request):
        return _error(404, "not_found", "The requested resource was not found.")
    return defaults.page_not_found(request, exception)


def server_error(request: HttpRequest) -> HttpResponse:
    if _is_api_request(request):
        return _error(500, "server_error", "Something went wrong on our side. Please try again.")
    return defaults.server_error(request)
