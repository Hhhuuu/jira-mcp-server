# Локальные окружения Jira MCP Server

## `.venv`

Для HTTP API и ручной отладки:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-build-isolation \
  -e jira-client \
  -e jira-readonly-service \
  -e jira-write-service \
  -e jira-mcp-server
```

Запуск HTTP API:

```bash
./scripts/run_api.sh
```

Проверка подключения:

```bash
curl http://127.0.0.1:8000/api/v1/me
```

Скрипт `run_api.sh` сначала пробует `.venv-mcp`, а если его нет — использует `.venv`.

## `.venv-mcp`

Для MCP:

```bash
python3.12 -m venv .venv-mcp
source .venv-mcp/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install --no-build-isolation \
  -e jira-client \
  -e jira-readonly-service \
  -e jira-write-service \
  -e jira-mcp-server
```

Запуск MCP:

```bash
./scripts/run_mcp.sh
```

## Если `python3.12` недоступен

Подойдёт любой Python `3.10+`.

Если локальный `venv` создаётся без `setuptools`, сначала установи его в окружение
или создай `venv` на базе уже подготовленного Python 3.10+ интерпретатора.
