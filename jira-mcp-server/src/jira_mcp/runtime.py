"""Runtime wiring для Jira HTTP API и MCP."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

from jira_readonly_service import JiraReadonlyService, load_app_config, load_secrets
from jira_write_service import JiraWriteService


def resolve_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _resolve_runtime_path(value: str | None, *default_parts: str) -> Path:
    if not value:
        return resolve_project_root().joinpath(*default_parts)

    path = Path(value)
    if path.is_absolute():
        return path
    return resolve_project_root() / path


def resolve_config_path() -> Path:
    value = os.getenv("JIRA_CONFIG_PATH")
    return _resolve_runtime_path(value, "config", "app.yaml")


def resolve_secrets_path() -> Path:
    value = os.getenv("JIRA_SECRETS_PATH")
    return _resolve_runtime_path(value, "secrets", "jira.yaml")


def load_runtime_service() -> JiraReadonlyService:
    app_config = load_app_config(resolve_config_path())
    secrets = load_secrets(resolve_secrets_path())
    return JiraReadonlyService.from_config(app_config, secrets)


def load_runtime_write_service() -> JiraWriteService:
    app_config = load_app_config(resolve_config_path())
    secrets = load_secrets(resolve_secrets_path())
    return JiraWriteService.from_config(app_config, secrets)
