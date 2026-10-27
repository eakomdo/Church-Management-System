import re
from io import StringIO
from unittest import mock

import pytest
from botocore.exceptions import ClientError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from storages.backends.s3 import S3Storage

from apps.core.files import (
    DOCUMENT_TYPES,
    IMAGE_TYPES,
    MB,
    FileTypeValidator,
    MaxFileSizeValidator,
    UploadPath,
)

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
PDF_BYTES = b"%PDF-1.7\n" + b"\x00" * 100
EXE_BYTES = b"MZ" + b"\x00" * 100


def upload(name: str, content: bytes) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, content)


class TestFileTypeValidator:
    def test_accepts_allowed_type(self):
        FileTypeValidator(IMAGE_TYPES)(upload("photo.png", PNG_BYTES))

    def test_checks_content_not_extension(self):
        with pytest.raises(ValidationError) as error:
            FileTypeValidator(IMAGE_TYPES)(upload("photo.jpg", EXE_BYTES))

        assert error.value.code == "file_type_not_allowed"

    def test_rejects_unrecognised_content(self):
        with pytest.raises(ValidationError):
            FileTypeValidator(DOCUMENT_TYPES)(upload("notes.pdf", b"just some text"))

    def test_pdf_allowed_for_documents_but_not_images(self):
        FileTypeValidator(DOCUMENT_TYPES)(upload("receipt.pdf", PDF_BYTES))
        with pytest.raises(ValidationError):
            FileTypeValidator(IMAGE_TYPES)(upload("receipt.pdf", PDF_BYTES))

    def test_rewinds_file_for_the_next_reader(self):
        file = upload("photo.png", PNG_BYTES)

        FileTypeValidator(IMAGE_TYPES)(file)

        assert file.read() == PNG_BYTES


class TestMaxFileSizeValidator:
    def test_accepts_file_at_the_limit(self):
        MaxFileSizeValidator(1 * MB)(upload("a.png", b"\x00" * MB))

    def test_rejects_file_over_the_limit_with_readable_message(self):
        with pytest.raises(ValidationError) as error:
            MaxFileSizeValidator(1 * MB)(upload("a.png", b"\x00" * (MB + 1)))

        assert error.value.code == "file_too_large"
        assert error.value.messages == ["File is too large. The limit is 1.0\xa0MB."]


class TestUploadPath:
    def test_replaces_name_with_uuid_under_dated_prefix(self):
        path = UploadPath("members/photos/")(None, "Kofi Mensah Ghana Card.JPG")

        assert re.fullmatch(r"members/photos/\d{4}/\d{2}/[0-9a-f-]{36}\.jpg", path)
        assert "Kofi" not in path

    def test_same_name_never_collides(self):
        upload_to = UploadPath("receipts")

        assert upload_to(None, "receipt.pdf") != upload_to(None, "receipt.pdf")


class TestCreateStorageBucketCommand:
    def test_skips_when_storage_is_not_s3(self):
        out = StringIO()

        call_command("create_storage_bucket", stdout=out)

        assert "nothing to create" in out.getvalue()

    def s3_storage(self, head_bucket_error: Exception | None = None) -> mock.MagicMock:
        storage = mock.MagicMock(spec=S3Storage)
        storage.bucket.name = "church-cms-dev"
        storage.connection.meta.client.head_bucket.side_effect = head_bucket_error
        return storage

    def test_creates_missing_bucket(self):
        missing = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
        storage = self.s3_storage(head_bucket_error=missing)

        with mock.patch(
            "apps.core.management.commands.create_storage_bucket.default_storage", storage
        ):
            call_command("create_storage_bucket", stdout=StringIO())

        storage.connection.meta.client.create_bucket.assert_called_once_with(
            Bucket="church-cms-dev"
        )

    def test_leaves_existing_bucket_alone(self):
        storage = self.s3_storage()

        with mock.patch(
            "apps.core.management.commands.create_storage_bucket.default_storage", storage
        ):
            call_command("create_storage_bucket", stdout=StringIO())

        storage.connection.meta.client.create_bucket.assert_not_called()
