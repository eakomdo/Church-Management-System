# pyright: reportArgumentType=false
# (django-environ annotates every `default=` as NoValue, so valid defaults fail type checks.)
"""Settings shared by every environment. Environment-specific modules import from here."""

from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]
THIRD_PARTY_APPS = [
    "ninja",
]
LOCAL_APPS = [
    "apps.core",
]
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=60)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# All branches are in Ghana today (spec section 4). Timestamps are stored in UTC.
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Accra"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploaded files: member photos, receipts, sermon audio. S3-compatible storage when a bucket is
# configured (SeaweedFS locally, S3 or R2 in production); local disk otherwise.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
S3_BUCKET = env("S3_BUCKET", default="")
if S3_BUCKET:
    default_storage = {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": S3_BUCKET,
            "endpoint_url": env("S3_ENDPOINT_URL", default=None),
            "access_key": env("S3_ACCESS_KEY"),
            "secret_key": env("S3_SECRET_KEY"),
            "region_name": env("S3_REGION", default="us-east-1"),
            "addressing_style": "path",
            "signature_version": "s3v4",
            # Files hold personal data, so they are private and served through signed links
            # that expire (NFR-01, NFR-02).
            "default_acl": None,
            "querystring_auth": True,
            "querystring_expire": 60 * 60,
            "file_overwrite": False,
        },
    }
else:
    default_storage = {"BACKEND": "django.core.files.storage.FileSystemStorage"}
STORAGES = {
    "default": default_storage,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# API
API_DOCS_ENABLED = env.bool("API_DOCS_ENABLED", default=True)
NINJA_PAGINATION_CLASS = "apps.core.pagination.PageNumberPagination"
NINJA_PAGINATION_PER_PAGE = 25
NINJA_PAGINATION_MAX_PER_PAGE_SIZE = 100

# Background jobs
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_TIMEZONE = TIME_ZONE
# Most tasks send messages or sync payments; callers never wait on a result.
CELERY_TASK_IGNORE_RESULT = True
# Acknowledge after the task finishes, so a worker crash re-queues the task instead of
# dropping it. Tasks must therefore be safe to run twice.
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_TIME_LIMIT = 10 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 9 * 60
CELERY_BEAT_SCHEDULE = {
    "clear-expired-sessions": {
        "task": "apps.core.tasks.clear_expired_sessions",
        "schedule": crontab(hour=2, minute=0),
    },
}
