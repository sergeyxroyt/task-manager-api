# task-manager-api

Task manager API built with Django and Django REST framework.

Swagger UI is available at `/api/schema`. The generated OpenAPI schema is
available at `/api/schema/openapi`.

## Features

- Create, edit, and delete tasks.
- Assign tasks to other users.
- Mark tasks as completed.
- Comment on tasks.

## Endpoints

Most API endpoints require JWT authentication.

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/auth/login/` | Obtain JWT tokens. |
| `POST` | `/api/auth/refresh/` | Refresh an access token. |
| `GET`, `POST` | `/api/tasks/` | List and create tasks. |
| `GET`, `PATCH`, `DELETE` | `/api/tasks/{task_id}/` | Retrieve, update, and delete a task. |
| `GET`, `POST` | `/api/tasks/{task_id}/comments/` | List and add comments. |
| `GET` | `/api/schema` | Swagger UI. |
| `GET` | `/api/schema/openapi` | OpenAPI schema. |
| — | `/admin/` | Django administration panel. |

## Authentication and authorization

The API uses JWT authentication. Obtain tokens with:

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"<username>","password":"<password>"}'
```

Use the returned access token for protected endpoints:

```text
Authorization: Bearer <access-token>
```

Refresh an expired access token by sending the refresh token to
`POST /api/auth/refresh/`. Task and comment endpoints are available only to
authenticated users. The `/admin/` endpoint uses Django permissions.

Create an administrator for the Django Admin with:

```bash
uv run python manage.py createsuperuser
```

## Requirements

- Python 3.14
- uv

## Local development

Before either option, create the environment file:

```bash
cp .env.example .env
```

### Docker Compose

Requirements: Docker with Docker Compose.

```bash
make dev-docker-up
```

The API is available at `http://localhost:8000`. To stop the services:

```bash
make dev-docker-down
```

### Separate application process

Requirements: Python 3.14, uv, and a running PostgreSQL instance available at
the `POSTGRES_HOST` and `POSTGRES_PORT` values from `.env`.

```bash
uv sync
make migrate
make dev-run
```

The API is available at `http://localhost:8000`.

## Useful commands

```bash
make test
make lint
make typecheck
```
