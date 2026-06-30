# Jira MCP Server: Запуск в Docker

## 1. Назначение

Этот документ описывает, как собрать и запустить `jira-mcp-server` в Docker.

Поддерживаются три режима:

- `http-api` — локальный HTTP API для ручной проверки
- `mcp-http` — MCP через streamable HTTP
- `mcp-stdio` — MCP через stdio

## 2. Что должно быть подготовлено

Перед запуском должны существовать:

- `config/app.yaml`
- `secrets/jira.yaml`

Шаблоны:

- `config/app.yaml.example`
- `secrets/jira.yaml.example`

Пример `config/app.yaml`:

```yaml
jira:
  base_url: "https://your-domain.atlassian.net"
  api_version: "3"
  deployment: "cloud"
  verify_ssl: true
```

Пример `secrets/jira.yaml`:

```yaml
jira:
  auth_type: "basic"
  username: "user@example.com"
  api_token: "your-atlassian-api-token"
```

## 3. Сборка образа

Из корня проекта:

```bash
docker build -t jira-mcp:local .
```

Если хочешь своё имя образа:

```bash
docker build -t my-company/jira-mcp:dev .
```

## 4. Запуск HTTP API

Этот режим нужен для:

- ручной отладки
- curl-запросов
- smoke-check

Команда:

```bash
docker run --rm -p 8000:8000 \
  -e JIRA_RUNTIME_MODE=http-api \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

После запуска доступны:

- `GET /health`
- `GET /api/v1/config`
- `GET /api/v1/me`
- `GET /api/v1/issue`
- `GET /api/v1/project`
- `GET /api/v1/search`
- `GET /api/v1/filters`
- `GET /api/v1/project/issue-types`
- `GET /api/v1/project/create-fields`
- `POST /api/v1/issue/create`
- `POST /api/v1/issue/comment`
- `POST /api/v1/issue/comment/update`
- `POST /api/v1/issue/description`
- `POST /api/v1/issue/labels`
- `POST /api/v1/issue/fields`

### Быстрая проверка

```bash
curl http://127.0.0.1:8000/health
```

```bash
curl http://127.0.0.1:8000/api/v1/me
```

```bash
curl "http://127.0.0.1:8000/api/v1/issue?issue_key=KAN-1"
```

## 5. Запуск MCP over HTTP

Этот режим нужен, если MCP-клиент умеет работать с HTTP transport.

Команда:

```bash
docker run --rm -p 8000:8000 \
  -e JIRA_RUNTIME_MODE=mcp-http \
  -e JIRA_MCP_HOST=0.0.0.0 \
  -e JIRA_MCP_PORT=8000 \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

## 6. Запуск MCP stdio

Этот режим нужен, если MCP-клиент запускает сервер как локальную команду.

Команда:

```bash
docker run --rm -i \
  -e JIRA_RUNTIME_MODE=mcp-stdio \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

## 7. Примеры подключения MCP-клиента через Docker

### Вариант 1. MCP stdio через `docker run`

Подходит для клиентов, которые умеют запускать локальную команду.

Пример конфигурации:

```json
{
  "mcpServers": {
    "jira-readonly": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "JIRA_RUNTIME_MODE=mcp-stdio",
        "-v",
        "./config:/app/config:ro",
        "-v",
        "./secrets:/app/secrets:ro",
        "jira-mcp:local"
      ]
    }
  }
}
```

Если MCP-клиент не любит относительные пути, используй абсолютные пути для volume mounts.

### Вариант 2. MCP over HTTP

Сначала подними контейнер:

```bash
docker run --rm -p 8000:8000 \
  -e JIRA_RUNTIME_MODE=mcp-http \
  -e JIRA_MCP_HOST=0.0.0.0 \
  -e JIRA_MCP_PORT=8000 \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

После этого MCP-клиент подключается к HTTP endpoint контейнера.

Если клиент ожидает URL, обычно используется адрес вида:

```text
http://127.0.0.1:8000/mcp
```

Если конкретный клиент требует другой формат MCP HTTP-конфигурации, укажи тот же базовый URL контейнера.

## 8. Какие переменные окружения поддерживаются

### Общие

- `JIRA_CONFIG_PATH`
- `JIRA_SECRETS_PATH`
- `JIRA_RUNTIME_MODE`

По умолчанию внутри контейнера используются:

- `/app/config/app.yaml`
- `/app/secrets/jira.yaml`

### Для HTTP API

- `JIRA_HTTP_HOST`
- `JIRA_HTTP_PORT`

По умолчанию:

- `JIRA_HTTP_HOST=0.0.0.0`
- `JIRA_HTTP_PORT=8000`

### Для MCP HTTP

- `JIRA_MCP_HOST`
- `JIRA_MCP_PORT`

По умолчанию:

- `JIRA_MCP_HOST=0.0.0.0`
- `JIRA_MCP_PORT=8000`

## 9. Безопасность

Реальные секреты не копируются в образ:

- `secrets/jira.yaml` исключён через `.dockerignore`

Поэтому секреты передаются только через volume mount:

```bash
-v "$(pwd)/secrets:/app/secrets:ro"
```

Это рекомендуемый способ и для локальной работы, и для CI/CD.

## 10. Типовой сценарий запуска

1. Создать `config/app.yaml`
2. Создать `secrets/jira.yaml`
3. Собрать образ:

```bash
docker build -t jira-mcp:local .
```

4. Поднять HTTP API:

```bash
docker run --rm -p 8000:8000 \
  -e JIRA_RUNTIME_MODE=http-api \
  -v "$(pwd)/config:/app/config:ro" \
  -v "$(pwd)/secrets:/app/secrets:ro" \
  jira-mcp:local
```

5. Проверить:

```bash
curl http://127.0.0.1:8000/api/v1/me
```

## 11. Типовые проблемы

### Контейнер стартует, но Jira не отвечает

Проверь:

- правильность `base_url`
- токен / логин
- доступность Jira из среды, где запускается Docker

### `/api/v1/me` возвращает `401`

Обычно это означает:

- неверный `api_token`
- неверный `username`
- выбран не тот `auth_type`

Для Jira Cloud обычно нужен:

- `auth_type: "basic"`
- `username: "<email>"`
- `api_token: "<atlassian token>"`

### MCP-клиент не умеет относительные пути

Тогда лучше:

- использовать локальный launcher `scripts/run_mcp.sh`
- либо запускать через Docker как фиксированную команду

## 12. Что дальше

После запуска на Docker можно:

- использовать HTTP API для ручной отладки
- подключить MCP-клиент к HTTP или stdio режиму
- использовать сохранённые JQL-фильтры и write-операции
