# Jira MCP Server: Документация для внешних потребителей

## 1. Назначение

`Jira MCP Server` — это MCP-сервер для работы с Jira.

Сервер позволяет:

- проверять подключение к Jira
- получать информацию о текущем пользователе
- читать задачи, проекты и результаты JQL-поиска
- хранить локальные именованные JQL-фильтры
- создавать Jira issue разных типов
- обновлять description, labels, comments и произвольные поля
- использовать markdown для description в Jira Cloud

Сервер поддерживает:

- `Jira Cloud`
- `Jira Server / Data Center`
- авторизацию через `email/login + API token`
- авторизацию через `bearer token`

## 2. Основные возможности

### Диагностика подключения

- `show_runtime_config`
- `get_current_user`

### Read-only сценарии

- `get_jira_issue`
- `get_jira_project`
- `search_jira_issues`

### Сохранённые JQL-фильтры

- `list_saved_jql_filters`
- `save_jql_filter`
- `delete_jql_filter`
- `search_jira_by_saved_filter`

### Create metadata

- `get_jira_create_issue_types`
- `get_jira_create_issue_fields`

### Write сценарии

- `create_jira_issue`
- `add_jira_comment`
- `update_jira_comment`
- `update_jira_description`
- `update_jira_description_from_markdown`
- `update_jira_labels`
- `update_jira_fields`

## 3. Поддерживаемые режимы Jira

### Jira Cloud

Используется:

- `base_url` вида `https://your-domain.atlassian.net`
- `deployment = "cloud"`

В этом режиме:

- issue/comment/description поддерживаются через Cloud REST API
- `description_markdown` и `description_markdown_file` конвертируются в ADF
- JQL search для Cloud использует актуальный endpoint `/rest/api/3/search/jql`

### Jira Server / Data Center

Используется:

- `base_url` вида `https://jira.example.local`
- `deployment = "server"`

В этом режиме:

- description отправляется как plain text
- search использует классический endpoint `/rest/api/{version}/search`

## 4. Поддерживаемые варианты авторизации

### Вариант 1. Basic auth с API token

Подходит для:

- Atlassian Jira Cloud

Используются:

- `auth_type = "basic"`
- `username` — обычно email
- `api_token`

Фактически клиент отправляет basic auth с `username + api_token`.

### Вариант 2. Bearer token

Подходит для:

- OAuth / service integrations
- некоторые server-установки

Используются:

- `auth_type = "bearer"`
- `bearer_token`
- при необходимости `cloud_id`

## 5. Конфигурация

### Файл `config/app.yaml`

Пример для Jira Cloud:

```yaml
jira:
  base_url: "https://your-domain.atlassian.net"
  api_version: "3"
  deployment: "cloud"
  verify_ssl: true

  filters:
    my_team:
      description: "Задачи моей команды"
      jql: 'project = KAN ORDER BY updated DESC'
      year_field: "created"

    my_team_by_year:
      description: "Задачи моей команды за выбранный год"
      jql_template: 'project = KAN AND created >= "{year}-01-01" AND created < "{next_year}-01-01" ORDER BY updated DESC'

  field_aliases:
    start_date: "customfield_10015"
    team: "customfield_10001"
```

### Файл `secrets/jira.yaml`

Пример для Cloud:

```yaml
jira:
  auth_type: "basic"
  username: "user@example.com"
  api_token: "your-atlassian-api-token"
```

Пример для bearer token:

```yaml
jira:
  auth_type: "bearer"
  bearer_token: "your-oauth-access-token"
  # cloud_id: "your-cloud-id"
```

## 6. Подключение MCP-сервера

В проекте уже есть файл `.mcp.json`, который описывает запуск сервера в `stdio`-режиме.

Базовая команда запуска:

```bash
.venv-mcp/bin/python -m jira_mcp
```

Если MCP-клиент поддерживает `command + args`, можно использовать такую конфигурацию:

```json
{
  "mcpServers": {
    "jira-readonly": {
      "command": ".venv-mcp/bin/python",
      "args": ["-m", "jira_mcp"],
      "env": {
        "JIRA_CONFIG_PATH": "config/app.yaml",
        "JIRA_SECRETS_PATH": "secrets/jira.yaml"
      }
    }
  }
}
```

Для Kilo можно подключить так:

```json
{
  "mcpServers": {
    "jira-readonly": {
      "type": "local",
      "workdir": "~/projects/jira-mcp-server",
      "command": ["~/projects/jira-mcp-server/scripts/run_mcp.sh"],
      "enabled": true
    }
  }
}
```

## 7. Описание MCP tools

### `show_runtime_config`

Назначение:

- показать, какие конфиги и секреты использует сервер

Вход:

- без параметров

Выход:

- пути к конфигу и секретам

Когда использовать:

- при первой настройке
- при отладке окружения

### `get_current_user`

Назначение:

- проверить авторизацию в Jira

Вход:

- без параметров

Выход:

- `accountId`
- `displayName`
- `emailAddress`
- `active`

Когда использовать:

- как smoke-check после настройки секретов

### `get_jira_issue`

Назначение:

- получить задачу Jira по key, id или Jira URL

Вход:

- `issue_key`
- `include_comments`
- `max_comments`

Выход:

- структурированные поля issue
- человекочитаемый `text`

Когда использовать:

- для чтения карточки задачи
- для быстрых agent workflows

### `get_jira_project`

Назначение:

- получить информацию о Jira project

Вход:

- `project_key`

Выход:

- `id`
- `key`
- `name`
- `projectTypeKey`

### `search_jira_issues`

Назначение:

- выполнить прямой JQL-поиск

Вход:

- `jql`
- `max_results`
- `start_at`

Выход:

- список задач
- нормализованный `text`

Когда использовать:

- если нужен произвольный JQL без сохранения фильтра

### `list_saved_jql_filters`

Назначение:

- показать локально сохранённые именованные фильтры

Вход:

- без параметров

Выход:

- список фильтров из `config/app.yaml`

### `save_jql_filter`

Назначение:

- создать или обновить локальный JQL-фильтр

Вход:

- `filter_name`
- `description`
- `jql` или `jql_template`
- `year_field`

Выход:

- сохранённый фильтр

### `delete_jql_filter`

Назначение:

- удалить локальный JQL-фильтр

Вход:

- `filter_name`

### `search_jira_by_saved_filter`

Назначение:

- выполнить поиск по локально сохранённому фильтру

Вход:

- `filter_name`
- `year` — опционально
- `max_results`
- `start_at`

Особенность:

- если фильтр хранит обычный `jql`, сервер может автоматически добавить ограничение по году через `year_field`
- если фильтр хранит `jql_template`, сервер подставит `{year}` и `{next_year}`

Пример:

- фильтр: `project = KAN ORDER BY updated DESC`
- запрос с `year = 2026`
- итоговый JQL:

```text
(project = KAN) AND created >= "2026-01-01" AND created < "2027-01-01" ORDER BY updated DESC
```

### `get_jira_create_issue_types`

Назначение:

- показать доступные issue types для создания задачи в проекте

Вход:

- `project_key`

Когда использовать:

- перед созданием issue
- чтобы не гадать по id/type name

### `get_jira_create_issue_fields`

Назначение:

- показать поля, доступные для create screen в `project + issue type`

Вход:

- `project_key`
- `issue_type`

Когда использовать:

- перед передачей custom fields
- для discovery системных и обязательных полей

### `create_jira_issue`

Назначение:

- создать новую Jira issue

Вход:

- `project_key`
- `summary`
- `issue_type`
- `description` — опционально
- `description_markdown` — опционально
- `description_markdown_file` — опционально
- `labels` — опционально
- `parent_issue_key` — опционально
- `fields` — опционально
- `custom_fields` — опционально

Особенности:

- `description_markdown` и `description_markdown_file` поддерживаются в Jira Cloud
- `custom_fields` и `fields` пропускаются через `field_aliases`, если алиасы настроены

### `add_jira_comment`

Назначение:

- добавить комментарий в issue

Вход:

- `issue_ref`
- `comment`

### `update_jira_comment`

Назначение:

- обновить существующий комментарий

Вход:

- `issue_ref`
- `comment_id`
- `comment`

### `update_jira_description`

Назначение:

- обновить description обычным текстом

Вход:

- `issue_ref`
- `description`

### `update_jira_description_from_markdown`

Назначение:

- обновить description из markdown

Вход:

- `issue_ref`
- `description_markdown` или `description_markdown_file`

### `update_jira_labels`

Назначение:

- добавить, удалить или полностью заменить labels

Вход:

- `issue_ref`
- `add_labels`
- `remove_labels`
- `set_labels`

### `update_jira_fields`

Назначение:

- обновить произвольные системные или custom поля

Вход:

- `issue_ref`
- `fields`
- `custom_fields`

Особенность:

- если в конфиге настроены `field_aliases`, можно передавать не только `customfield_12345`, но и человекочитаемые имена вроде `start_date`

## 8. Markdown в description

Поддерживаемый поднабор markdown для Jira Cloud:

- заголовки
- абзацы
- списки
- bold / italic
- inline code
- fenced code blocks
- ссылки
- blockquote

Ограничения:

- поддержка таблиц и сложной вложенности сейчас `best effort`
- это не полноценный markdown editor для Jira, а практичный bridge для описаний

## 9. Алиасы полей

Если в конфиге указано:

```yaml
jira:
  field_aliases:
    start_date: customfield_10015
    team: customfield_10001
```

то в `update_jira_fields` или `create_jira_issue` можно передавать:

```json
{
  "custom_fields": {
    "start_date": "2026-07-02",
    "team": "some-team-id"
  }
}
```

Сервер сам преобразует эти ключи в реальные Jira field ids.

## 10. Рекомендуемый порядок интеграции

1. Настроить `config/app.yaml`
2. Настроить `secrets/jira.yaml`
3. Проверить `get_current_user`
4. Проверить `get_jira_project`
5. Для write-сценариев сначала вызвать:
   - `get_jira_create_issue_types`
   - `get_jira_create_issue_fields`
6. Только потом:
   - создавать issue
   - обновлять description / labels / comments / custom fields

## 11. Ограничения текущей версии

- write-сценарии не валидируют каждое custom field значение по create metadata до отправки в Jira; финальная валидация остаётся за Jira
- markdown в description покрывает только базовый поднабор
- сохранённые JQL-фильтры хранятся локально в `config/app.yaml`, а не как Jira saved filters
- если MCP-клиент плохо работает с относительными путями, лучше использовать `scripts/run_mcp.sh`
