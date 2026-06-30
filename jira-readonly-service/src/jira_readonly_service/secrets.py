"""Загрузка секретов Jira."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, ValidationError

from .exceptions import InvalidSecretsError, SecretsFileNotFoundError


class JiraSecrets(BaseModel):
    """Секреты доступа к Jira."""

    auth_type: str = "basic"
    username: Optional[str] = None
    api_token: Optional[str] = None
    bearer_token: Optional[str] = None
    cloud_id: Optional[str] = None


class SecretsFile(BaseModel):
    """Корневой YAML секретов."""

    jira: JiraSecrets


def load_secrets(path: str | Path) -> JiraSecrets:
    secrets_path = Path(path)
    if not secrets_path.exists() or not secrets_path.is_file():
        raise SecretsFileNotFoundError(secrets_path)

    try:
        payload = yaml.safe_load(secrets_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise InvalidSecretsError(
            f"Файл secrets/jira.yaml содержит некорректный YAML: {exc}"
        ) from exc
    except OSError as exc:
        raise InvalidSecretsError(f"Не удалось прочитать secrets/jira.yaml: {exc}") from exc

    if not isinstance(payload, dict):
        raise InvalidSecretsError(
            "Некорректный формат secrets/jira.yaml: корневой YAML должен быть объектом."
        )

    try:
        secrets = SecretsFile.model_validate(payload).jira
    except ValidationError as exc:
        raise InvalidSecretsError(f"Некорректный формат secrets/jira.yaml: {exc}") from exc

    if secrets.auth_type not in {"basic", "bearer"}:
        raise InvalidSecretsError("jira.auth_type должен быть basic или bearer.")
    if secrets.auth_type == "basic" and (not secrets.username or not secrets.api_token):
        raise InvalidSecretsError("Для auth_type=basic нужны username и api_token.")
    if secrets.auth_type == "bearer" and not secrets.bearer_token:
        raise InvalidSecretsError("Для auth_type=bearer нужен bearer_token.")
    return secrets
