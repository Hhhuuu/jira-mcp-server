# План миграции `jira` на Python

## 1. Что это за проект сейчас

Текущий `jira` — это не Maven-плагин и не Java-сервис, а уже отдельный Node.js MCP-сервер.

Фактически это компактный read-only сервис с одним use case:

- `get_jira_issue`

Сейчас почти вся логика собрана в одном файле:

- `src/index.js`

Внутри него смешаны:

- загрузка env-конфига
- сборка auth headers
- логирование
- HTTP-клиент Jira
- нормализация входного `issueKey`
- преобразование Jira/ADF в читаемый текст
- MCP stdio transport
- MCP HTTP transport

## 2. Что реально нужно перенести

### Обязательное

- конфигурацию Jira Cloud / Jira Server
- basic auth и bearer auth
- read-only Jira client
- нормализацию `issueKey` и Jira URL
- чтение задачи по key/id
- опциональную загрузку комментариев
- упрощение Jira issue JSON до удобной структуры
- преобразование ADF/HTML в текст
- MCP tool `get_jira_issue`
- HTTP API для ручной проверки

### Что не нужно переносить 1:1

- Node.js runtime
- `dotenv/config` как обязательный механизм
- `zod`
- ручную сборку MCP-сервера в одном файле
- `node_modules`

## 3. Бизнес-сценарий проекта

На текущем этапе сценарий один:

1. Пользователь передаёт ключ задачи, id или Jira URL
2. Сервис извлекает нормализованный `issueRef`
3. Сервис запрашивает Jira REST API
4. Сервис приводит ответ к читаемой структуре
5. Сервис возвращает:
   - человекочитаемый текст
   - structured content

Это хороший кандидат на очень компактную Python-архитектуру.

## 4. Аналогия с текущим Python-подходом

По аналогии с `confluence-mcp-server` я бы раскладывал проект так:

- `jira-client`
- `jira-readonly-service`
- `jira-mcp-server`

Если позже появятся write-сценарии или отдельный ADF bridge, тогда можно расширить:

- `jira-adf-service`
- `jira-write-service`

Но сейчас это преждевременно.

## 5. Целевая структура проекта

```text
jira-python/
  jira-client/
  jira-readonly-service/
  jira-mcp-server/
  config/
  secrets/
  scripts/
  README.md
  LOCAL_ENVIRONMENTS.md
  .mcp.json
```

## 6. Разделение по пакетам

### `jira-client`

Назначение:

- изолировать работу с Jira REST API

Сюда:

- `JiraClientConfig`
- `JiraClient`
- auth header logic
- сборка `apiBaseUrl`
- `get_issue(...)`
- общие HTTP-ошибки
- модели ответа Jira

### `jira-readonly-service`

Назначение:

- use case слой поверх клиента

Сюда:

- `normalize_issue_ref(...)`
- `get_jira_issue(...)`
- `simplify_issue(...)`
- `format_issue(...)`
- `adf_to_text(...)`
- `strip_html(...)`
- DTO request/response
- config loader
- secrets loader

### `jira-mcp-server`

Назначение:

- transport layer

Сюда:

- MCP tools
- HTTP API
- runtime wiring
- launcher scripts

## 7. Как разложить текущий `index.js`

### В `jira-client`

Из `src/index.js` сюда переедут:

- `loadConfig()` частично
- `normalizeBaseUrl()`
- `normalizeApiVersion()`
- `jiraRequest()`
- `getIssue()`
- сборка `authHeader`

### В `jira-readonly-service`

Сюда переедут:

- `normalizeIssueRef()`
- `simplifyIssue()`
- `pickName()`
- `pickUser()`
- `adfToText()`
- `visitAdf()`
- `stripHtml()`
- `formatIssue()`

### В `jira-mcp-server`

Сюда переедут:

- `createJiraMcpServer()`
- `startServer()`
- `startHttpServer()`

И отдельно:

- HTTP endpoint `/health`
- HTTP endpoint вида `/api/v1/issue`

## 8. Конфигурация в Python

Я бы делал так же, как в `confluence-mcp-server`:

- `config/app.yaml`
- `secrets/jira.yaml`

### `config/app.yaml`

```yaml
jira:
  base_url: "https://your-domain.atlassian.net"
  api_version: "3"
  deployment: "cloud"
  verify_ssl: true
```

### `secrets/jira.yaml`

```yaml
jira:
  auth_type: "basic"
  username: "you@example.com"
  api_token: "your-atlassian-api-token"
```

Или bearer:

```yaml
jira:
  auth_type: "bearer"
  bearer_token: "..."
  cloud_id: "..."
```

## 9. Целевая логика auth

Нужно поддержать два режима:

### Basic

- `username + api_token`

### Bearer

- `bearer_token`
- для Jira Cloud OAuth:
  - `apiBaseUrl = https://api.atlassian.com/ex/jira/<cloud_id>`

Это полностью соответствует текущей Node-логике.

## 10. Какой HTTP API дать поверх сервиса

По аналогии с текущим Confluence-проектом:

- `GET /health`
- `GET /api/v1/config`
- `GET /api/v1/issue`

Например:

```text
GET /api/v1/issue?issue_key=PROJ-123&include_comments=true&max_comments=5
```

## 11. Какие MCP tools нужны в первой версии

Минимально:

- `show_runtime_config`
- `get_jira_issue`

Опционально полезно:

- `get_current_auth_mode`
- `normalize_issue_ref`

Но в первой версии можно оставить только:

- `get_jira_issue`

## 12. Что важно сохранить из текущего поведения

- поддержка issue key, numeric id и Jira URL
- поддержка `selectedIssue=...`
- comments как опция
- `maxComments` с ограничением
- ADF -> plain text
- fallback для HTML description
- read-only nature сервиса

## 13. Что я бы улучшил при миграции

### 1. Разделить клиент и use case

Сейчас это смешано в `index.js`.

### 2. Сделать нормальные typed exceptions

Например:

- `JiraConfigError`
- `JiraAuthenticationError`
- `JiraRequestError`
- `JiraIssueNotFoundError`

### 3. Сделать единый runtime слой

Так же, как в `confluence-mcp-server`:

- config path resolution
- secrets path resolution
- launcher script
- project-level `.mcp.json`

### 4. Сделать переносимый stdio launcher

Чтобы на другой машине не приходилось править пути в MCP-клиенте.

## 14. Предлагаемый порядок миграции

### Этап 1. `jira-client`

Сделать:

- config model
- auth model
- `JiraClient`
- `get_issue(...)`

### Этап 2. `jira-readonly-service`

Сделать:

- `normalize_issue_ref`
- `simplify_issue`
- `adf_to_text`
- `format_issue`
- request/response DTO

### Этап 3. HTTP API

Сделать:

- `GET /health`
- `GET /api/v1/config`
- `GET /api/v1/issue`

И сначала руками проверить сервис через API.

### Этап 4. MCP layer

Сделать:

- stdio MCP
- HTTP MCP
- `.mcp.json`
- launcher script

## 15. Что не делать сейчас

- write-операции в Jira
- создание задач
- переходы статусов
- работа с Jira search/JQL
- вложения
- редактирование полей

Это всё можно добавлять потом как отдельные use case’ы.

## 16. Рекомендуемая целевая итоговая форма

Для текущего scope я бы считал удачной такую структуру:

```text
jira-python/
  jira-client/
  jira-readonly-service/
  jira-mcp-server/
  config/
  secrets/
  scripts/
  .mcp.json
  README.md
  LOCAL_ENVIRONMENTS.md
```

Идея такая же, как в `confluence-mcp-server`:

- transport тонкий
- клиент отдельный
- use case отдельный
- конфиг и секреты вынесены
- ручная проверка через HTTP API до MCP
