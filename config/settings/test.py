from .base import *  # noqa: F403

DEBUG = False

# Hashing with the production algorithm makes every test that creates a user slow.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Run tasks inline so tests see their effects without a broker.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
