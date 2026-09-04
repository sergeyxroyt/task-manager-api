# Manual API test plan

## Purpose

Проверить вручную рабочие endpoint’ы задач и комментариев task-manager-api.
Endpoint’ы получения/обновления JWT, Django Admin и OpenAPI/Swagger в этот
план не входят.

## Preconditions

```sh
export BASE_URL="http://localhost:8000"
export API="$BASE_URL/api"
```

Запустить окружение одним из вариантов:

```sh
cp .env.example .env
make dev-docker-up
```

или при отдельно запущенном PostgreSQL:

```sh
uv sync
make migrate
make dev-run
```

Перед началом убедиться, что сервер отвечает:

```sh
test "$(curl -sS -o /dev/null -w '%{http_code}' "$API/tasks/")" = 401
```

Все запросы ниже должны иметь заголовок `Content-Type: application/json`, если
у запроса есть JSON-тело. Все проверяемые endpoint’ы защищены JWT. Поэтому
перед тестированием получить access token подготовительным login-запросом
(сам `/api/auth/login/` этим планом не тестируется):

```sh
export ACCESS_TOKEN="$(curl -sS -X POST "$API/auth/login/" \
  -H 'Content-Type: application/json' \
  -d '{"username":"api_creator","password":"Creator-pass-123!"}' \
  | uv run python -c 'import json,sys; print(json.load(sys.stdin)["access"])')"
test -n "$ACCESS_TOKEN"
```

Для защищённых ресурсов использовать:

```sh
export AUTH="Authorization: Bearer $ACCESS_TOKEN"
```

Ожидаемый результат каждого шага нужно фиксировать как `PASS`/`FAIL` с HTTP
статусом и фактическим JSON-ответом. Значения `USER_ID`, `ASSIGNEE_ID`,
`TASK_ID`, `TASK_2_ID`, `COMMENT_ID` и токены брать из фактических ответов, а не
предполагать заранее.

## Test data setup

Создать двух активных пользователей. Команда безопасна для повторного запуска:
существующие пользователи с такими username обновляются.

```sh
uv run python manage.py shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); u,_=U.objects.get_or_create(username='api_creator',defaults={'email':'api_creator@example.com','is_active':True}); u.set_password('Creator-pass-123!'); u.is_active=True; u.save(); a,_=U.objects.get_or_create(username='api_assignee',defaults={'email':'api_assignee@example.com','is_active':True}); a.set_password('Assignee-pass-123!'); a.is_active=True; a.save(); print({'creator_id':u.pk,'assignee_id':a.pk})"
```

После подготовки сохранить идентификаторы:

```sh
export CREATOR_USERNAME="api_creator"
export CREATOR_PASSWORD="Creator-pass-123!"
export ASSIGNEE_ID="<id из вывода команды>"
```

## 1. Unauthenticated access

Без `Authorization` проверить:

```sh
curl -i "$API/tasks/"
curl -i "$API/tasks/1/"
curl -i "$API/tasks/1/comments/"
```

PASS criteria: каждый ответ `401`; данные задач/комментариев не возвращаются.

Также проверить malformed header (`Authorization: Bearer invalid`) и другой
scheme (`Authorization: Basic abc`): ожидать `401`.

## 2. Tasks

### 3.1 Create task — default fields

```sh
curl -i -X POST "$API/tasks/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"title":"API task default"}'
```

PASS criteria: `201`; ответ ровно содержит числовой `id`. Сохранить как
`TASK_ID`. Затем получить его через detail и проверить: title совпадает,
description равен пустой строке, status равен `todo`, `creator_id` равен ID
creator, `assignee_id` равен `null`, `created_at` и `updated_at` — ISO datetime.

### 3.2 Create task — complete valid body

```sh
curl -i -X POST "$API/tasks/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d "{\"title\":\"Assigned API task\",\"description\":\"Initial description\",\"assignee_id\":$ASSIGNEE_ID}"
```

Сохранить returned id как `TASK_2_ID`. Через detail проверить все поля,
включая `assignee_id == ASSIGNEE_ID` и `status == "todo"`.

### 3.3 Create task — validation and assignee errors

Проверить POST с каждым телом: `{}`, `{"title":""}`, title длиной 256
символов, `title: null`, `description: null`, `assignee_id: 0`,
`assignee_id: -1`, `assignee_id: "text"`, несуществующий положительный
`assignee_id`.

PASS criteria: первые validation cases возвращают `400` с ошибками полей;
несуществующий assignee возвращает `404` с `detail == "Assignee not found."`;
невалидные запросы не создают task.

### 3.4 List tasks — default, pagination and filters

```sh
curl -i "$API/tasks/" -H "$AUTH"
curl -i "$API/tasks/?limit=1&offset=0" -H "$AUTH"
curl -i "$API/tasks/?limit=1&offset=1" -H "$AUTH"
curl -i "$API/tasks/?statuses=todo" -H "$AUTH"
curl -i "$API/tasks/?status=todo&status=done" -H "$AUTH"
curl -i "$API/tasks/?statuses=todo,done" -H "$AUTH"
```

PASS criteria: `200`; JSON имеет `data` (array) и `pagination` с числовыми
`page`, `per_page`, `total`, `total_pages`; default `per_page == 20`, `page`
нумеруется с 1; limit/offset и статусы реально влияют на выдачу; в статусном
фильтре нет задач с другим status. Порядок — от новых к старым.

Проверить query validation: `limit=0`, `limit=101`, `limit=text`, `offset=-1`,
`offset=text`, `statuses=unknown`. PASS criteria: `400`, данные не возвращаются.
Проверить `offset` за пределами total: `200`, пустой `data`, корректные metadata.

### 3.5 Get task

```sh
curl -i "$API/tasks/$TASK_ID/" -H "$AUTH"
curl -i "$API/tasks/999999/" -H "$AUTH"
```

PASS criteria: существующий task даёт `200` со всеми полями схемы; неизвестный
ID даёт `404` и `detail == "Task not found."`; `0`/нечисловой path не даёт
успешный ответ (`404`).

### 3.6 Patch task — each supported behavior

Последовательно выполнять PATCH и после каждого делать GET:

```sh
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{"title":"Renamed task"}'
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{"description":"Updated description","status":"in_progress"}'
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d "{\"assignee_id\":$ASSIGNEE_ID}"
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{"assignee_id":null}'
curl -i -X PATCH "$API/tasks/$TASK_ID/" -H "$AUTH" -H 'Content-Type: application/json' -d '{}'
```

PASS criteria: каждый запрос `204` с пустым телом; изменяется только переданное
поле, пропущенные поля сохраняются; `status` принимает `todo`, `in_progress`,
`done`; null снимает assignee; `updated_at` обновляется после изменения.
Для `{}` проверить фактическое поведение и зафиксировать его отдельно как
контракт текущей версии.

Проверить invalid PATCH: неизвестное поле, `title: null`, title длиной 256,
неподдерживаемый status, `assignee_id: 0`, несуществующий assignee и PATCH
несуществующего task. Ожидать `400` для validation, `404` с
`Assignee not found.` для неизвестного assignee и `404` с `Task not found.` для
неизвестного task; при ошибке состояние task не меняется.

### 3.7 Delete task

Перед удалением убедиться, что `TASK_2_ID` имеет комментарий (см. раздел 4),
затем:

```sh
curl -i -X DELETE "$API/tasks/$TASK_2_ID/" -H "$AUTH"
curl -i "$API/tasks/$TASK_2_ID/" -H "$AUTH"
curl -i -X DELETE "$API/tasks/$TASK_2_ID/" -H "$AUTH"
```

PASS criteria: первый DELETE `204` с пустым телом; GET после удаления `404`
(`Task not found.`); повторный DELETE `404`. Проверить, что комментарии удалённой
задачи больше недоступны (cascade).

## 3. Comments

### 4.1 Create comments

```sh
curl -i -X POST "$API/tasks/$TASK_ID/comments/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"content":"First API comment"}'
curl -i -X POST "$API/tasks/$TASK_ID/comments/" -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"content":"Second API comment"}'
```

PASS criteria: каждый ответ `201`, ровно содержит числовой `id`; сохранить id
первого как `COMMENT_ID`. GET списка должен показывать author_id текущего
пользователя, task не меняется.

Проверить `{}`, `content: null`, `content: 123`, пустую строку, пробелы,
многострочный текст, Unicode и длинный текст. Зафиксировать фактическую
валидацию: `CharField` допускает пустую строку, если сервер не ограничивает её
отдельно. Для неизвестного task ожидать `404` и `Task not found.`.

### 4.2 List comments, pagination and task existence

```sh
curl -i "$API/tasks/$TASK_ID/comments/" -H "$AUTH"
curl -i "$API/tasks/$TASK_ID/comments/?limit=1&offset=0" -H "$AUTH"
curl -i "$API/tasks/$TASK_ID/comments/?limit=1&offset=1" -H "$AUTH"
curl -i "$API/tasks/999999/comments/" -H "$AUTH"
```

PASS criteria: `200`; response has `data` and pagination metadata; comments
ordered newest first (`Second API comment`, then `First API comment`); limit and
offset are respected; unknown task gives `404` with `Task not found.`. Проверить
`limit=0`, `limit=101`, `offset=-1`, non-numeric values — ожидать `400`.

## 4. Final consistency checks

1. Снова получить список задач и убедиться, что удалённый `TASK_2_ID` отсутствует.
2. Получить комментарии `TASK_ID` и сверить `total` с числом элементов/созданных
   комментариев с учётом pagination.
3. Повторить один защищённый GET с новым access из refresh — должен быть `200`.
4. Убедиться, что каждый запрос без JWT не раскрыл данные и каждый ответ `204`
   не содержит body.
5. В отчёте указать дату, commit/version, URL, окружение, фактические IDs,
   результаты каждого раздела и тело всех FAIL-ответов.
