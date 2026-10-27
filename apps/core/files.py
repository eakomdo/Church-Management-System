"""Upload validation and storage paths shared by every model that stores files."""

import uuid
from pathlib import PurePath

import filetype
from django.core.exceptions import ValidationError
from django.core.files import File
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.deconstruct import deconstructible

MB = 1024 * 1024

IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
DOCUMENT_TYPES = IMAGE_TYPES | {"application/pdf"}

MAX_IMAGE_SIZE = 5 * MB
MAX_DOCUMENT_SIZE = 10 * MB


@deconstructible
class MaxFileSizeValidator:
    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes

    def __call__(self, file: File) -> None:
        if file.size is not None and file.size > self.max_bytes:
            raise ValidationError(
                "File is too large. The limit is %(limit)s.",
                code="file_too_large",
                params={"limit": filesizeformat(self.max_bytes)},
            )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, MaxFileSizeValidator) and other.max_bytes == self.max_bytes


@deconstructible
class FileTypeValidator:
    """Checks the file's leading bytes, not its name, so a renamed .exe can't pass as a .jpg."""

    def __init__(self, allowed_types: frozenset[str]) -> None:
        self.allowed_types = allowed_types

    def __call__(self, file: File) -> None:
        file.seek(0)
        kind = filetype.guess(file.read(261))  # 261 bytes covers every signature filetype knows
        file.seek(0)
        if kind is None or kind.mime not in self.allowed_types:
            raise ValidationError(
                "Unsupported file type. Allowed: %(allowed)s.",
                code="file_type_not_allowed",
                params={"allowed": ", ".join(sorted(self.allowed_types))},
            )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FileTypeValidator) and other.allowed_types == self.allowed_types


image_validators = [MaxFileSizeValidator(MAX_IMAGE_SIZE), FileTypeValidator(IMAGE_TYPES)]
document_validators = [MaxFileSizeValidator(MAX_DOCUMENT_SIZE), FileTypeValidator(DOCUMENT_TYPES)]


@deconstructible
class UploadPath:
    """``upload_to`` that stores files as ``<prefix>/<year>/<month>/<uuid><ext>``.

    The original name is dropped: it can carry personal details ("kofi-mensah-ghana-card.jpg")
    and two uploads with the same name would otherwise collide.
    """

    def __init__(self, prefix: str) -> None:
        self.prefix = prefix.strip("/")

    def __call__(self, instance: object, filename: str) -> str:
        extension = PurePath(filename).suffix.lower()
        now = timezone.now()
        return f"{self.prefix}/{now:%Y/%m}/{uuid.uuid7()}{extension}"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UploadPath) and other.prefix == self.prefix
