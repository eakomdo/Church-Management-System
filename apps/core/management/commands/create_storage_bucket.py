from botocore.exceptions import ClientError
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand
from storages.backends.s3 import S3Storage


class Command(BaseCommand):
    help = "Create the S3 bucket for uploaded files if it does not exist yet."

    def handle(self, *args, **options) -> None:
        if not isinstance(default_storage, S3Storage):
            self.stdout.write("Default storage is not S3; nothing to create.")
            return

        client = default_storage.connection.meta.client
        bucket = default_storage.bucket.name
        try:
            client.head_bucket(Bucket=bucket)
        except ClientError:
            client.create_bucket(Bucket=bucket)
            self.stdout.write(self.style.SUCCESS(f"Created bucket {bucket}."))
        else:
            self.stdout.write(f"Bucket {bucket} already exists.")
