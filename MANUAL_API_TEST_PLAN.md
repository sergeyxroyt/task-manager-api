# Manual API test plan

## Purpose

Manually verify the task and comment endpoints of task-manager-api. JWT token
obtain/refresh endpoints, Django Admin, and OpenAPI/Swagger are not covered by
this plan.

## Preconditions

```sh
export BASE_URL="http://localhost:8000"
export API="$BASE_URL/api"
```

Start the environment using one of the following options:

```sh
cp .env.example .env
make dev-docker-up
```

or with PostgreSQL running separately:

```sh
uv sync
make migrate
make dev-run
```

Before starting, make sure that the server responds:

```sh
test "$(curl -sS -o /dev/null -w '%{http_code}' "$API/tasks/")" = 401
```

All requests below must include the `Content-Type: application/json` header if
the request has a JSON body. All endpoints under test are protected by JWT.
Therefore, obtain an access token before testing by sending a preparatory login
request (the `/api/auth/login/` endpoint itself is not tested by this plan):

```sh
export ACCESS_TOKEN="$(curl -sS -X POST "$API/auth/login/" \
  -H 'Content-Type: application/json' \
  -d '{"username":"api_creator","password":"Creator-pass-123!"}' \
  | uv run python -c 'import json,sys; print(json.load(sys.stdin)["access"])')"
test -n "$ACCESS_TOKEN"
```

Use the following header for protected resources:

```sh
export AUTH="Authorization: Bearer $ACCESS_TOKEN"
```

Record the expected result of each step as `PASS`/`FAIL`, including the HTTP
status and the actual JSON response. Take the values of `USER_ID`,
`ASSIGNEE_ID`, `TASK_ID`, `TASK_2_ID`, `COMMENT_ID`, and tokens from the actual
responses rather than assuming them in advance.

## Test data setup

Create two active users. This command is safe to run repeatedly: existing users
with these usernames are updated.

```sh
uv run python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); u,_=U.objects.get_or_create(username='api_creator',defaults={'email':'api_creator@example.com','is_active':True}); u.set_password('Creator-pass-123!'); u.is_active=True; u.save(); a,_=U.objects.get_or_create(username='api_assignee',defaults={'email':'api_assignee@example.com','is_active':True}); a.set_password('Assignee-pass-123!'); a.is_active=True; a.save(); print({'creator_id':u.pk,'assignee_id':a.pk})"
```

After setup, save the identifiers:

```sh
export CREATOR_USERNAME="api_creator"
export CREATOR_PASSWORD="Creator-pass-123!"
export ASSIGNEE_ID="<id from the command output>"
```

## 1. Unauthenticated access

Check the following without an `Authorization` header:

```sh
curl -i "$API/tasks/"
curl -i "$API/tasks/1/"
curl -i "$API/tasks/1/comments/"
```

PASS criteria: every response is `401`; no task or comment data is returned.

Also test a malformed header (`Authorization: Bearer invalid`) and a different
scheme (`Authorization: Basic abc`); expect `401`.

## 2. Tasks

### 2.1 Create task — default fields

```sh
curl -i -X POST "$API/tasks/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"title":"API task default"}'
```

PASS criteria: `201`; the response contains exactly a numeric `id`. Save it as
`TASK_ID`. Then retrieve it through the detail endpoint and verify: the title
matches, the description is an empty string, the status is `todo`,
`creator_id` is the creator's ID, `assignee_id` is `null`, and `created_at` and
`updated_at` are ISO datetimes.

### 2.2 Create task — complete valid body

```sh
curl -i -X POST "$API/tasks/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"title\":\"Assigned API task\",\"description\":\"Initial description\",\"assignee_id\":$ASSIGNEE_ID}"
```

Save the returned ID as `TASK_2_ID`. Verify all fields through the detail
endpoint, including `assignee_id == ASSIGNEE_ID` and `status == "todo"`.

### 2.3 Create task — validation and assignee errors

Test POST with each of the following bodies: `{}`, `{"title":""}`, a title
with 256 characters, `title: null`, `description: null`, `assignee_id: 0`,
`assignee_id: -1`, `assignee_id: "text"`, and a non-existent positive
`assignee_id`.

PASS criteria: the first validation cases return `400` with field errors; a
non-existent assignee returns `404` with `detail == "Assignee not found."`;
invalid requests do not create a task.

### 2.4 List tasks — default, pagination, and filters

```sh
curl -i "$API/tasks/" -H "$AUTH"
curl -i "$API/tasks/?limit=1&offset=0" -H "$AUTH"
curl -i "$API/tasks/?limit=1&offset=1" -H "$AUTH"
curl -i "$API/tasks/?statuses=todo" -H "$AUTH"
curl -i "$API/tasks/?status=todo&status=done" -H "$AUTH"
curl -i "$API/tasks/?statuses=todo,done" -H "$AUTH"
```

PASS criteria: `200`; the JSON has `data` (an array) and `pagination` with
numeric `page`, `per_page`, `total`, and `total_pages`; the default `per_page`
is `20`, and `page` is numbered from 1; limit/offset and statuses affect the
result; the status-filtered result contains no tasks with another status.
Results are ordered from newest to oldest.

Test query validation: `limit=0`, `limit=101`, `limit=text`, `offset=-1`,
`offset=text`, and `statuses=unknown`. PASS criteria: `400`; no data is
returned. Test an offset beyond the total: `200`, an empty `data`, and correct
metadata.

### 2.5 Get task

```sh
curl -i "$API/tasks/$TASK_ID/" -H "$AUTH"
curl -i "$API/tasks/999999/" -H "$AUTH"
```

PASS criteria: an existing task returns `200` with all schema fields; an
unknown ID returns `404` and `detail == "Task not found."`; `0` and a
non-numeric path do not return a successful response (`404`).

### 2.6 Patch task — each supported behavior

Run the PATCH requests in sequence and perform a GET after each one:

```sh
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{"title":"Renamed task"}'
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{"description":"Updated description","status":"in_progress"}'
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d "{\"assignee_id\":$ASSIGNEE_ID}"
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{"assignee_id":null}'
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{}'
```

PASS criteria: every request returns `204` with an empty body; only the supplied
field changes, and omitted fields are preserved; `status` accepts `todo`,
`in_progress`, and `done`; `null` removes the assignee; `updated_at` changes
after an update. For `{}`, verify the actual behavior and record it separately
as a contract of the current version.

Test invalid PATCH requests: an unknown field, `title: null`, a title with 256
characters, an unsupported status, `assignee_id: 0`, a non-existent assignee,
and a PATCH for a non-existent task. Expect `400` for validation errors, `404`
with `Assignee not found.` for an unknown assignee, and `404` with `Task not
found.` for an unknown task; the task state must not change on error.

### 2.7 Delete task

Before deletion, make sure that `TASK_2_ID` has a comment (see section 3), then:

```sh
curl -i -X DELETE "$API/tasks/$TASK_2_ID/" -H "$AUTH"
curl -i "$API/tasks/$TASK_2_ID/" -H "$AUTH"
curl -i -X DELETE "$API/tasks/$TASK_2_ID/" -H "$AUTH"
```

PASS criteria: the first DELETE returns `204` with an empty body; the GET after
deletion returns `404` (`Task not found.`); the repeated DELETE returns `404`.
Verify that comments belonging to the deleted task are no longer available
(cascade).

## 3. Comments

### 3.1 Create comments

```sh
curl -i -X POST "$API/tasks/$TASK_ID/comments/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"content":"First API comment"}'
curl -i -X POST "$API/tasks/$TASK_ID/comments/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"content":"Second API comment"}'
```

PASS criteria: every response returns `201` and contains exactly a numeric
`id`; save the first ID as `COMMENT_ID`. The list GET must show the current
user's `author_id`; the task must not change.

Test `{}`, `content: null`, `content: 123`, an empty string, whitespace,
multiline text, Unicode, and long text. Record the actual validation behavior:
`CharField` allows an empty string unless the server restricts it separately.
For an unknown task, expect `404` and `Task not found.`.

### 3.2 List comments, pagination, and task existence

```sh
curl -i "$API/tasks/$TASK_ID/comments/" -H "$AUTH"
curl -i "$API/tasks/$TASK_ID/comments/?limit=1&offset=0" -H "$AUTH"
curl -i "$API/tasks/$TASK_ID/comments/?limit=1&offset=1" -H "$AUTH"
curl -i "$API/tasks/999999/comments/" -H "$AUTH"
```

PASS criteria: `200`; the response has `data` and pagination metadata; comments
are ordered newest first (`Second API comment`, then `First API comment`); limit
and offset are respected; an unknown task returns `404` with `Task not found.`.
Test `limit=0`, `limit=101`, `offset=-1`, and non-numeric values; expect `400`.

## 4. Final consistency checks

1. Retrieve the task list again and make sure the deleted `TASK_2_ID` is absent.
2. Retrieve the comments for `TASK_ID` and compare `total` with the number of
   elements/created comments, accounting for pagination.
3. Repeat a protected GET with a new access token obtained through refresh; it
   must return `200`.
4. Make sure that no request without JWT exposed data and that every `204`
   response has no body.
5. In the report, include the date, commit/version, URL, environment, actual
   IDs, the result of each section, and the body of every FAIL response.
