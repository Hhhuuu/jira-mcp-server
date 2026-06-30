"""Загрузка прикладного конфига Jira."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from .exceptions import ConfigFileNotFoundError, InvalidConfigError


class JiraAppConfig(BaseModel):
    """Конфиг Jira."""

    base_url: str
    api_version: str = "3"
    deployment: str = "cloud"
    verify_ssl: bool = True


class AppConfig(BaseModel):
    """Корневой конфиг приложения."""

    jira: JiraAppConfig


def load_app_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists() or not config_path.is_file():
        raise ConfigFileNotFoundError(config_path)

    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise InvalidConfigError(f"Файл config/app.yaml содержит некорректный YAML: {exc}") from exc
    except OSError as exc:
        raise InvalidConfigError(f"Не удалось прочитать config/app.yaml: {exc}") from exc

    if not isinstance(payload, dict):
        raise InvalidConfigError("Некорректный формат config/app.yaml: корневой YAML должен быть объектом.")

    try:
        config = AppConfig.model_validate(payload)
    except ValidationError as exc:
        raise InvalidConfigError(f"Некорректный формат config/app.yaml: {exc}") from exc

    if config.jira.api_version not in {"2", "3"}:
        raise InvalidConfigError("jira.api_version должен быть 2 или 3.")
    if config.jira.deployment not in {"cloud", "server"}:
        raise InvalidConfigError("jira.deployment должен быть cloud или server.")
    return config
