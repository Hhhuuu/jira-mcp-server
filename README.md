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
- MCP tool `show_runtime_config`
- MCP tool `get_current_user`
- MCP tool `get_jira_issue`

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

## Важно

- `confluence-mcp-server` не трогаем
- текущий `jira` не переписываем на месте
- вся новая разработка идёт только в этой папке
