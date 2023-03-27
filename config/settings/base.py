"""Settings shared by every environment.

Nothing in this module may contain a credential. Every value that differs
between a laptop and a server is read from the environment through the
helpers below, so that the same image can be promoted from dev to prod.

Environment-specific modules (``local``, ``production``) import ``*`` from
here and then override.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# config/settings/base.py -> config/settings -> config -> <repo root>
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# A .env file is optional; real deployments inject environment variables
# directly. Values already present in the environment always win.
load_dotenv(BASE_DIR / ".env", override=False)


def env(name: str, default: str | None = None) -> str | None:
    """Read a string environment variable."""
    return os.environ.get(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    """Read a boolean environment variable ("1", "true", "yes" are true)."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated environment variable into a list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return int(raw)


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

# No default: every environment module must supply one. ``local`` falls back to
# an obviously-insecure development key; ``production`` refuses to start
# without a real one.
SECRET_KEY = env("DJANGO_SECRET_KEY")

DEBUG = env_bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "profiles.UserProfile"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
]

LOCAL_APPS = [
    "interview.core",
    "interview.profiles",
    "interview.inventory",
    "interview.order",
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

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
#
# Postgres when POSTGRES_DB is set, SQLite otherwise. The SQLite fallback keeps
# the test suite and a first `runserver` working with zero infrastructure; the
# docker-compose stack sets the Postgres variables.

if env("POSTGRES_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER", "postgres"),
            "PASSWORD": env("POSTGRES_PASSWORD", ""),
            "HOST": env("POSTGRES_HOST", "127.0.0.1"),
            "PORT": env("POSTGRES_PORT", "5432"),
            # Reuse connections instead of opening one per request.
            "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": env("SQLITE_PATH", str(BASE_DIR / "db.sqlite3")),
        }
    }


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static and media
# ---------------------------------------------------------------------------
#
# STATIC_ROOT is a build artefact produced by `collectstatic`; it is generated,
# never committed, and therefore lives outside the app packages.

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / env("MEDIA_ROOT", "media")


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
#
# Every list endpoint is paginated by default: an unbounded list is the single
# most common way a small API falls over once real data arrives.

INVENTORY_PAGE_SIZE = env_int("INVENTORY_PAGE_SIZE", 3)

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "interview.core.pagination.DefaultLimitOffsetPagination",
    "PAGE_SIZE": env_int("API_PAGE_SIZE", 25),
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", "INFO"),
    },
    "loggers": {
        "interview": {
            "handlers": ["console"],
            "level": env("APP_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}
