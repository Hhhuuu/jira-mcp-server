"""Загрузка прикладного конфига Jira."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

from .exceptions import ConfigFileNotFoundError, InvalidConfigError, SavedFilterNotFoundError


class JiraSavedFilterConfig(BaseModel):
    """Именованный JQL-фильтр."""

    description: Optional[str] = None
    jql: Optional[str] = None
    jql_template: Optional[str] = None
    year_field: str = "created"


class JiraAppConfig(BaseModel):
    """Конфиг Jira."""

    base_url: str
    api_version: str = "3"
    deployment: str = "cloud"
    verify_ssl: bool = True
    filters: Dict[str, JiraSavedFilterConfig] = Field(default_factory=dict)
    field_aliases: Dict[str, str] = Field(default_factory=dict)


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
    for filter_name, filter_config in config.jira.filters.items():
        if not filter_config.jql and not filter_config.jql_template:
            raise InvalidConfigError(
                f"Фильтр jira.filters.{filter_name} должен содержать jql или jql_template."
            )
    return config


def save_app_config(path: str | Path, config: AppConfig) -> None:
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(mode="python", exclude_none=True)
    try:
        config_path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as exc:
        raise InvalidConfigError(f"Не удалось записать config/app.yaml: {exc}") from exc


def list_saved_filters(config: AppConfig) -> Dict[str, JiraSavedFilterConfig]:
    return dict(config.jira.filters)


def get_saved_filter(config: AppConfig, filter_name: str) -> JiraSavedFilterConfig:
    filter_config = config.jira.filters.get(filter_name)
    if not filter_config:
        raise SavedFilterNotFoundError(filter_name)
    return filter_config
