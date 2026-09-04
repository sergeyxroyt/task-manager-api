FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src

EXPOSE 8000

ENV WEB_CONCURRENCY=2

CMD ["sh", "-c", "exec uv run gunicorn config.wsgi:application --chdir /app/src --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY}"]
