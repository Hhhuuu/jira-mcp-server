#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

VENV_PYTHON="${PROJECT_ROOT}/.venv-mcp/bin/python"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
fi

CONFIG_PATH="${JIRA_CONFIG_PATH:-${PROJECT_ROOT}/config/app.yaml}"
SECRETS_PATH="${JIRA_SECRETS_PATH:-${PROJECT_ROOT}/secrets/jira.yaml}"
HOST="${JIRA_API_HOST:-127.0.0.1}"
PORT="${JIRA_API_PORT:-8000}"

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Не найден интерпретатор локального окружения: ${PROJECT_ROOT}/.venv-mcp/bin/python" >&2
  echo "Создай .venv-mcp или .venv и установи зависимости перед запуском API." >&2
  exit 1
fi

export JIRA_CONFIG_PATH="${CONFIG_PATH}"
export JIRA_SECRETS_PATH="${SECRETS_PATH}"

exec "${VENV_PYTHON}" -m uvicorn jira_mcp.api:app --app-dir "${PROJECT_ROOT}/jira-mcp-server/src" --host "${HOST}" --port "${PORT}"
