FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/README.md ./apps/api/
COPY apps/api/src ./apps/api/src
RUN pip install ./apps/api

COPY apps/api/alembic.ini ./apps/api/alembic.ini
COPY apps/api/migrations ./apps/api/migrations
COPY packages/scenarios/catalog ./packages/scenarios/catalog

RUN useradd --create-home --uid 10001 arena \
    && mkdir -p /app/runtime \
    && chown -R arena:arena /app
USER arena
WORKDIR /app/apps/api

EXPOSE 8000
CMD ["uvicorn", "arena.interfaces.http.app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
