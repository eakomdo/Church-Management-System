from celery import shared_task
from django.core.management import call_command


@shared_task
def clear_expired_sessions() -> None:
    """Sessions live in the database; without this they grow forever."""
    call_command("clearsessions")
