# Jira MCP Server

## Целевая структура

- `jira-client` — клиент для Jira REST API
- `jira-readonly-service` — read-only use case слой
- `jira-mcp-server` — HTTP API и MCP transport
- `config` — прикладной конфиг
- `secrets` — секреты подключения
- `scripts` — launcher-скрипты

## План миграции

Подробный план лежит в:

- `PYTHON_MIGRATION_PLAN.md`

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
- MCP tool `show_runtime_config`
- MCP tool `get_current_user`
- MCP tool `get_jira_issue`
- MCP tool `get_jira_project`
- MCP tool `search_jira_issues`
- MCP tool `list_saved_jql_filters`
- MCP tool `save_jql_filter`
- MCP tool `delete_jql_filter`
- MCP tool `search_jira_by_saved_filter`

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

## Важно

- `confluence-mcp-server` не трогаем
- текущий `jira` не переписываем на месте
- вся новая разработка идёт только в этой папке
