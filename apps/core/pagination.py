from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Schema
from ninja import pagination as ninja_pagination


class PageNumberPagination(ninja_pagination.PageNumberPagination):
    """Ninja's page-number pagination, echoing the page and page size back to the client.

    Response shape: ``{"items": [...], "count": 312, "page": 2, "page_size": 25}``.
    Sizes are capped by ``NINJA_PAGINATION_MAX_PER_PAGE_SIZE``.
    """

    # Ninja reads the nested Output schema by design, so overriding it is intended.
    class Output(Schema):  # pyright: ignore[reportIncompatibleVariableOverride]
        items: list[Any]
        count: int
        page: int
        page_size: int

    def paginate_queryset(
        self,
        queryset: QuerySet,
        pagination: ninja_pagination.PageNumberPagination.Input,
        request: HttpRequest,
        **params: Any,
    ) -> Any:
        result = super().paginate_queryset(queryset, pagination, request, **params)
        return self._with_page_info(result, pagination)

    async def apaginate_queryset(
        self,
        queryset: QuerySet,
        pagination: ninja_pagination.PageNumberPagination.Input,
        request: HttpRequest,
        **params: Any,
    ) -> Any:
        result = await super().apaginate_queryset(queryset, pagination, request, **params)
        return self._with_page_info(result, pagination)

    def _with_page_info(
        self, result: dict[str, Any], pagination: ninja_pagination.PageNumberPagination.Input
    ) -> dict[str, Any]:
        return {
            **result,
            "page": pagination.page,
            "page_size": self._get_page_size(pagination.page_size),
        }
