# Jira MCP Server

## Целевая структура

- `jira-client` — клиент для Jira REST API
- `jira-readonly-service` — read-only use case слой
- `jira-write-service` — write use case слой
- `jira-mcp-server` — HTTP API и MCP transport
- `config` — прикладной конфиг
- `secrets` — секреты подключения
- `scripts` — launcher-скрипты

## План миграции

Подробный план лежит в:

- `PYTHON_MIGRATION_PLAN.md`

## Дополнительная документация

- `EXTERNAL_CONSUMERS.md` — документация для внешних потребителей
- `LOCAL_ENVIRONMENTS.md` — настройка локальных окружений

## Docker

Собрать образ:

```bash
docker build -t jira-mcp:local .
```

Запуск HTTP API:

```bash
docker run --rm -p 8000:8000 \
  -e JIRA_RUNTIME_MODE=http-api \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

Запуск MCP over HTTP:

```bash
docker run --rm -p 8000:8000 \
  -e JIRA_RUNTIME_MODE=mcp-http \
  -e JIRA_MCP_HOST=0.0.0.0 \
  -e JIRA_MCP_PORT=8000 \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

Запуск MCP stdio:

```bash
docker run --rm -i \
  -e JIRA_RUNTIME_MODE=mcp-stdio \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

## Принцип работы

1. Сначала переносим клиент Jira
2. Потом переносим read-only бизнес-логику
3. Потом даём HTTP API для ручной проверки
4. Только после этого добавляем MCP-обёртку

## Что уже работает

- `GET /health`
- `GET /api/v1/config`
- `GET /api/v1/me`
- `GET /api/v1/issue?issue_key=...`
- `GET /api/v1/project?project_key=...`
- `GET /api/v1/search?jql=...`
- `GET /api/v1/filters`
- `POST /api/v1/filters`
- `DELETE /api/v1/filters?filter_name=...`
- `GET /api/v1/filters/search?filter_name=...&year=2026`
- `GET /api/v1/project/issue-types?project_key=...`
- `GET /api/v1/project/create-fields?project_key=...&issue_type=...`
- `POST /api/v1/issue/create`
- `POST /api/v1/issue/comment`
- `POST /api/v1/issue/comment/update`
- `POST /api/v1/issue/description`
- `POST /api/v1/issue/labels`
- `POST /api/v1/issue/fields`
- MCP tool `show_runtime_config`
- MCP tool `get_current_user`
- MCP tool `get_jira_issue`
- MCP tool `get_jira_project`
- MCP tool `search_jira_issues`
- MCP tool `list_saved_jql_filters`
- MCP tool `save_jql_filter`
- MCP tool `delete_jql_filter`
- MCP tool `search_jira_by_saved_filter`
- MCP tool `get_jira_create_issue_types`
- MCP tool `get_jira_create_issue_fields`
- MCP tool `create_jira_issue`
- MCP tool `add_jira_comment`
- MCP tool `update_jira_comment`
- MCP tool `update_jira_description`
- MCP tool `update_jira_labels`
- MCP tool `update_jira_fields`

## Быстрый smoke-test

После настройки `config/app.yaml` и `secrets/jira.yaml`:

```bash
./scripts/run_api.sh
```

Проверка подключения без знания issue key:

```bash
curl http://127.0.0.1:8000/api/v1/me
```

Проверка чтения задачи:

```bash
curl "http://127.0.0.1:8000/api/v1/issue?issue_key=PROJ-123"
```

Проверка поиска по сохранённому фильтру:

```bash
curl "http://127.0.0.1:8000/api/v1/filters/search?filter_name=my_team&year=2026"
```

Проверка create metadata:

```bash
curl "http://127.0.0.1:8000/api/v1/project/issue-types?project_key=KAN"
curl "http://127.0.0.1:8000/api/v1/project/create-fields?project_key=KAN&issue_type=Задача"
```

Создание задачи:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/issue/create \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "KAN",
    "summary": "Пример задачи из API",
    "issue_type": "Задача",
    "description": "Описание новой задачи",
    "labels": ["python-mcp"]
  }'
```

Создание задачи с markdown-описанием из файла:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/issue/create \
  -H "Content-Type: application/json" \
  -d '{
    "project_key": "KAN",
    "summary": "Задача с markdown description",
    "issue_type": "Задача",
    "description_markdown_file": "tmp-description.md"
  }'
```

Обновление описания, labels и комментариев:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/issue/description \
  -H "Content-Type: application/json" \
  -d '{"issue_ref":"KAN-4","description":"Новое описание"}'

curl -X POST http://127.0.0.1:8000/api/v1/issue/description \
  -H "Content-Type: application/json" \
  -d '{"issue_ref":"KAN-4","description_markdown_file":"tmp-description.md"}'

curl -X POST http://127.0.0.1:8000/api/v1/issue/labels \
  -H "Content-Type: application/json" \
  -d '{"issue_ref":"KAN-4","add_labels":["verified"]}'

curl -X POST http://127.0.0.1:8000/api/v1/issue/comment \
  -H "Content-Type: application/json" \
  -d '{"issue_ref":"KAN-4","comment":"Комментарий из API"}'
```

## Алиасы полей

В `config/app.yaml` можно задать человекочитаемые алиасы для системных и custom полей:

```yaml
jira:
  field_aliases:
    start_date: customfield_10015
    team: customfield_10001
```

После этого в `fields` или `custom_fields` можно передавать:

```json
{
  "issue_ref": "KAN-4",
  "custom_fields": {
    "start_date": "2026-07-02"
  }
}
```

Сервис сам преобразует `start_date` в `customfield_10015`.

## Markdown в description

Для Jira Cloud поддерживаются:

- `description` — обычный текст
- `description_markdown` — markdown-строка
- `description_markdown_file` — путь до markdown-файла

Markdown сейчас конвертируется в ADF с поддержкой базовых конструкций:

- заголовки
- абзацы
- списки
- bold / italic
- inline code
- fenced code blocks
- ссылки
- blockquote

## Сохранённые фильтры

Локальные именованные JQL-фильтры хранятся в `config/app.yaml`.

Можно:

- хранить базовый `jql`
- хранить `jql_template` с параметрами `{year}` и `{next_year}`
- задавать `year_field`, если годовое ограничение нужно добавлять автоматически

Пример:

```yaml
jira:
  filters:
    my_team:
      description: "Задачи моей команды"
      jql: 'project = KAN ORDER BY updated DESC'
      year_field: "created"
```

Тогда запрос "дай мне задачи за 2026 год по фильтру `my_team`" превращается в:

```text
(project = KAN) AND created >= "2026-01-01" AND created < "2027-01-01" ORDER BY updated DESC
```