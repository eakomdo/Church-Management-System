import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.testing import TestClient

from apps.core.errors import Conflict, NotFound, register_exception_handlers

api = NinjaAPI(urls_namespace="errors-test")
register_exception_handlers(api)


@api.get("/not-found")
def raise_not_found(request):
    raise NotFound("Member not found.")


@api.get("/conflict")
def raise_conflict(request):
    raise Conflict(details={"field": "phone"})


@api.get("/http-404")
def raise_http_404(request):
    raise Http404


@api.get("/permission-denied")
def raise_permission_denied(request):
    raise PermissionDenied


@api.get("/throttled")
def raise_http_error(request):
    raise HttpError(429, "Slow down.")


@api.get("/crash")
def crash(request):
    raise RuntimeError("database password is hunter2")


@api.get("/service-field-error")
def raise_field_validation_error(request):
    raise ValidationError(
        {"phone": ValidationError("This phone number is already in use.", code="unique")}
    )


@api.get("/service-error")
def raise_validation_error(request):
    raise ValidationError("Pledge end date is before its start date.")


@api.get("/typed")
def typed(request, count: int):
    return {"count": count}


client = TestClient(api)


@pytest.mark.parametrize(
    ("path", "status", "code", "message"),
    [
        ("/not-found", 404, "not_found", "Member not found."),
        ("/http-404", 404, "not_found", "The requested resource was not found."),
        (
            "/permission-denied",
            403,
            "permission_denied",
            "You do not have permission to perform this action.",
        ),
        ("/throttled", 429, "throttled", "Slow down."),
    ],
)
def test_errors_share_one_envelope(path, status, code, message):
    response = client.get(path)

    assert response.status_code == status
    assert response.json() == {"error": {"code": code, "message": message, "details": None}}


def test_api_error_details_reach_the_client():
    response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json()["error"]["details"] == {"field": "phone"}


def test_validation_error_lists_the_invalid_fields():
    response = client.get("/typed?count=many")

    body = response.json()["error"]
    assert response.status_code == 422
    assert body["code"] == "validation_error"
    assert body["details"][0]["loc"] == ["query", "count"]


def test_service_field_errors_use_the_same_details_shape():
    response = client.get("/service-field-error")

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"loc": ["phone"], "msg": "This phone number is already in use.", "type": "unique"}
    ]


def test_service_non_field_error_has_empty_location():
    response = client.get("/service-error")

    assert response.status_code == 422
    assert response.json()["error"]["details"] == [
        {"loc": [], "msg": "Pledge end date is before its start date.", "type": "invalid"}
    ]


def test_unexpected_error_is_hidden_from_the_client(caplog):
    response = client.get("/crash")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "server_error"
    assert "hunter2" not in response.content.decode()
    assert "Unhandled API error" in caplog.text


def test_unknown_api_url_returns_json_404(client):
    # Uses Django's test client so the request goes through URL routing, not straight to Ninja.
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_unknown_site_url_keeps_html_404(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response["Content-Type"].startswith("text/html")
