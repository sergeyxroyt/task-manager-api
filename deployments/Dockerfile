FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "config.asgi:application", "--app-dir", "/app/src", "--host", "0.0.0.0", "--port", "8000"]
