"""Guards on the settings module itself.

The repository's history shows `SECRET_KEY = os.environ.get("SECRET_KEY")`
being replaced by a hardcoded literal. These tests make that regression fail
loudly instead of shipping quietly.
"""

import importlib
import re

import pytest
from django.core.exceptions import ImproperlyConfigured

from config.settings import base


def _base_source() -> str:
    from pathlib import Path

    return Path(base.__file__).read_text()


def test_base_settings_contain_no_hardcoded_secret_key():
    source = _base_source()

    assignment = re.search(r"^SECRET_KEY\s*=\s*(.+)$", source, flags=re.MULTILINE)
    assert assignment is not None
    assert "env(" in assignment.group(1), "SECRET_KEY must be read from the environment"


def test_base_settings_contain_no_hardcoded_database_password():
    source = _base_source()

    assert '"PASSWORD": env(' in source
    assert not re.search(r'"PASSWORD":\s*"[^"]+"', source)


def test_production_requires_a_secret_key(monkeypatch):
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")

    with pytest.raises(ImproperlyConfigured):
        importlib.reload(importlib.import_module("config.settings.production"))


def test_production_requires_allowed_hosts(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "a-real-key")
    monkeypatch.delenv("DJANGO_ALLOWED_HOSTS", raising=False)

    with pytest.raises(ImproperlyConfigured):
        importlib.reload(importlib.import_module("config.settings.production"))


def test_production_locks_the_api_down(monkeypatch):
    monkeypatch.setenv("DJANGO_SECRET_KEY", "a-real-key")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "example.com")

    production = importlib.reload(importlib.import_module("config.settings.production"))

    assert production.DEBUG is False
    assert production.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"] == [
        "rest_framework.permissions.IsAuthenticated"
    ]
    assert production.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] == [
        "rest_framework.renderers.JSONRenderer"
    ]
    assert production.SESSION_COOKIE_SECURE is True
    assert production.CSRF_COOKIE_SECURE is True
    assert production.SECURE_HSTS_SECONDS > 0


def test_base_dir_points_at_the_repository_root():
    """It used to resolve to `config/`, one directory too deep."""
    assert (base.BASE_DIR / "manage.py").exists()


def test_env_helpers():
    import os

    os.environ["_TEST_FLAG"] = "YES"
    os.environ["_TEST_LIST"] = "a, b ,c"
    os.environ["_TEST_INT"] = "42"
    try:
        assert base.env_bool("_TEST_FLAG") is True
        assert base.env_bool("_TEST_MISSING", default=True) is True
        assert base.env_list("_TEST_LIST") == ["a", "b", "c"]
        assert base.env_list("_TEST_MISSING") == []
        assert base.env_int("_TEST_INT", 0) == 42
        assert base.env_int("_TEST_MISSING", 7) == 7
    finally:
        for key in ("_TEST_FLAG", "_TEST_LIST", "_TEST_INT"):
            os.environ.pop(key, None)


def test_pagination_is_on_by_default():
    assert base.REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"].endswith("DefaultLimitOffsetPagination")
