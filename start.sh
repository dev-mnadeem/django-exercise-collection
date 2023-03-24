#!/bin/bash
#
# Create a virtualenv, install dependencies, migrate and load the demo data.
# Safe to re-run: the seed command is idempotent.
#
# With no POSTGRES_DB set the project falls back to SQLite, so this works with
# or without the docker-compose database running.

set -euo pipefail

VENV_DIR="${VENV_DIR:-.venv}"

echo "Setting up venv in $VENV_DIR..."
python3 -m venv "$VENV_DIR"
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements-dev.txt

echo "Migrating..."
python manage.py migrate --noinput

echo "Loading demo data..."
python manage.py seed_demo_data

echo
echo "Done. Activate the venv with: source $VENV_DIR/bin/activate"
echo "Then run the API with:        python manage.py runserver"
