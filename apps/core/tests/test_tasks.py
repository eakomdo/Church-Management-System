from datetime import timedelta

import pytest
from django.contrib.sessions.models import Session
from django.utils import timezone

from apps.core.tasks import clear_expired_sessions
from config.celery import app


@pytest.mark.django_db
def test_clear_expired_sessions_keeps_active_ones():
    now = timezone.now()
    Session.objects.create(session_key="expired", session_data="", expire_date=now - timedelta(1))
    Session.objects.create(session_key="active", session_data="", expire_date=now + timedelta(1))

    clear_expired_sessions.delay()

    assert list(Session.objects.values_list("session_key", flat=True)) == ["active"]


def test_scheduled_tasks_point_at_registered_tasks():
    app.loader.import_default_modules()
    for entry in app.conf.beat_schedule.values():
        assert entry["task"] in app.tasks
