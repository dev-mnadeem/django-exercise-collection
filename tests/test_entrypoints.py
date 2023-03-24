"""The WSGI and ASGI entrypoints must load on their own default settings.

pytest-django sets ``DJANGO_SETTINGS_MODULE`` before any test runs, which would
hide a wrong default, so each entrypoint is imported in a fresh interpreter
with the variable removed.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("module", ["config.wsgi", "config.asgi"])
def test_entrypoint_loads_with_its_default_settings(module):
    env = {k: v for k, v in os.environ.items() if k != "DJANGO_SETTINGS_MODULE"}

    result = subprocess.run(
        [sys.executable, "-c", f"import {module} as m; print(type(m.application).__name__)"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
    assert "Handler" in result.stdout
