"""Abstract base models. Every domain model in the project inherits from ``BaseModel``."""

import uuid

from django.conf import settings
from django.db import models


class UUIDModel(models.Model):
    """UUIDv7 primary key.

    v7 IDs start with a timestamp, so new rows land at the end of the index like an
    auto-increment key would, while staying unguessable in URLs and safe to generate on a
    phone before it syncs (offline capture, NFR-07).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """UUID key, timestamps, and who created and last changed the row.

    Services set ``created_by`` and ``updated_by`` explicitly from the acting user. Users are
    deactivated, never deleted, so these keys PROTECT rather than lose the history.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )

    class Meta:
        abstract = True
