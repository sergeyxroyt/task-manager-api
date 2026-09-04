# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    WEB_CONCURRENCY=2

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY manage.py ./
COPY gunicorn.conf.py ./

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--pythonpath", "/app/src", "--config", "/app/gunicorn.conf.py"]
