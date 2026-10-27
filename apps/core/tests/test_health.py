from unittest import mock

import pytest
from django.db import OperationalError

from apps.core.api import database_is_reachable

pytestmark = pytest.mark.django_db


def test_health_reports_ok_when_database_is_reachable(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_503_envelope_when_database_is_down(client):
    with mock.patch("apps.core.api.database_is_reachable", return_value=False):
        response = client.get("/api/v1/health")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"


def test_database_probe_reports_failure_instead_of_raising():
    with mock.patch("apps.core.api.connection.cursor", side_effect=OperationalError):
        assert database_is_reachable() is False
