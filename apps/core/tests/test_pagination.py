from ninja import NinjaAPI
from ninja.pagination import paginate
from ninja.testing import TestClient

from apps.core.errors import register_exception_handlers

api = NinjaAPI(urls_namespace="pagination-test")
register_exception_handlers(api)


@api.get("/numbers", response=list[int])
@paginate
def numbers(request):
    return list(range(60))


client = TestClient(api)


def test_first_page_uses_default_page_size():
    body = client.get("/numbers").json()

    assert body == {"items": list(range(25)), "count": 60, "page": 1, "page_size": 25}


def test_requested_page_and_size_are_echoed_back():
    body = client.get("/numbers?page=2&page_size=10").json()

    assert body["items"] == list(range(10, 20))
    assert (body["page"], body["page_size"]) == (2, 10)


def test_page_size_is_capped_at_the_maximum():
    body = client.get("/numbers?page_size=500").json()

    assert body["page_size"] == 100
    assert len(body["items"]) == 60


def test_page_past_the_end_is_empty():
    body = client.get("/numbers?page=9").json()

    assert body["items"] == []
    assert body["count"] == 60


def test_page_zero_is_rejected():
    response = client.get("/numbers?page=0")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
