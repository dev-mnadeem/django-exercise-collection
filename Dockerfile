# syntax=docker/dockerfile:1

# ---------------------------------------------------------------------------
# Stage 1: build wheels
#
# psycopg2-binary and Pillow both ship wheels, but building them in a separate
# stage means a compiler is never present in the image that actually runs.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /wheels

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements-prod.txt ./
RUN pip wheel --wheel-dir /wheels/dist -r requirements-prod.txt


# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production

# libpq5 is the runtime half of libpq-dev; curl backs the HEALTHCHECK below.
RUN apt-get update \
    && apt-get install --no-install-recommends -y libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --create-home app

WORKDIR /app

COPY --from=builder /wheels/dist /wheels/dist
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-index --find-links=/wheels/dist -r requirements-prod.txt \
    && rm -rf /wheels

COPY --chown=app:app manage.py ./
COPY --chown=app:app config ./config
COPY --chown=app:app interview ./interview

# collectstatic needs a key and a host but touches no database, so a throwaway
# pair is enough here; the real values arrive as environment variables at run
# time.
RUN DJANGO_SECRET_KEY=build-time-only \
    DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput \
    && mkdir -p /app/media \
    && chown -R app:app /app/staticfiles /app/media

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/healthz/ || exit 1

# Two workers by default; size WEB_CONCURRENCY to the container's CPU limit.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-2} --timeout ${WEB_TIMEOUT:-30} --access-logfile - --error-logfile -"]
