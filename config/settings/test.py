from .base import *  # noqa: F403

DEBUG = False

# Hashing with the production algorithm makes every test that creates a user slow.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
