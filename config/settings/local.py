"""Development settings.

Safe defaults so that `./manage.py runserver` works on a fresh clone with no
environment file at all. Nothing here is suitable for a public deployment.
"""

from .base import *  # noqa: F401,F403
from .base import env, env_bool, env_list

DEBUG = env_bool("DJANGO_DEBUG", default=True)

# An obviously-fake key: it is a development placeholder, not a credential.
# `production.py` refuses to start without a real DJANGO_SECRET_KEY.
SECRET_KEY = env("DJANGO_SECRET_KEY") or "django-insecure-local-development-key-not-for-deployment"

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1],testserver")
