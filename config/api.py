from django.conf import settings
from ninja import NinjaAPI

from apps.core.api import router as core_router
from apps.core.errors import register_exception_handlers

api = NinjaAPI(
    title="Church Management System API",
    version="1",
    urls_namespace="api-v1",
    docs_url="/docs" if settings.API_DOCS_ENABLED else None,
)
register_exception_handlers(api)

api.add_router("/", core_router)
