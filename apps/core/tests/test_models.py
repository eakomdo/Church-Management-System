import time

import pytest
from django.db import connection, models
from django.test.utils import isolate_apps

from apps.core.models import BaseModel, TimeStampedModel, UUIDModel


@pytest.fixture
def note_model():
    """A throwaway concrete model with a real table, torn down with the test transaction."""
    with isolate_apps("apps.core"):

        class Note(UUIDModel, TimeStampedModel):
            text = models.CharField(max_length=50)

            class Meta:
                app_label = "core"

        with connection.schema_editor() as editor:
            editor.create_model(Note)
        yield Note


@pytest.mark.django_db
def test_ids_are_time_ordered_uuid7(note_model):
    first = note_model.objects.create(text="first")
    second = note_model.objects.create(text="second")

    assert first.id.version == 7
    assert first.id < second.id


@pytest.mark.django_db
def test_timestamps_are_set_on_create_and_refreshed_on_save(note_model):
    note = note_model.objects.create(text="draft")
    created_at = note.created_at
    assert note.updated_at >= created_at

    time.sleep(0.01)
    note.text = "final"
    note.save()

    assert note.created_at == created_at
    assert note.updated_at > created_at


def test_audit_user_keys_protect_history():
    for name in ("created_by", "updated_by"):
        field = BaseModel._meta.get_field(name)
        assert isinstance(field, models.ForeignKey)
        relation = field.remote_field
        assert isinstance(relation, models.ManyToOneRel)
        assert relation.on_delete is models.PROTECT
        assert field.null
        assert not field.editable
