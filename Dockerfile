FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY backend ./backend
RUN pip install .
COPY scenarios ./scenarios
COPY alembic.ini ./
COPY alembic ./alembic

RUN useradd --create-home --uid 10001 arena \
    && mkdir -p /app/runtime \
    && chown -R arena:arena /app
USER arena

EXPOSE 8000
CMD ["uvicorn", "arena.api:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
