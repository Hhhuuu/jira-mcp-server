"""Исключения конфигурации и сервисного слоя Jira."""

from __future__ import annotations

from pathlib import Path


class JiraReadonlyServiceError(Exception):
    """Базовое исключение read-only сервиса Jira."""


class ConfigFileNotFoundError(JiraReadonlyServiceError):
    """Не найден файл конфигурации."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            f"Не найден файл конфигурации: {path}. Создайте его на основе config/app.yaml.example."
        )


class SecretsFileNotFoundError(JiraReadonlyServiceError):
    """Не найден файл секретов."""

    def __init__(self, path: Path) -> None:
        super().__init__(
            f"Не найден файл секретов: {path}. Создайте его на основе secrets/jira.yaml.example."
        )


class InvalidConfigError(JiraReadonlyServiceError):
    """Некорректный прикладной конфиг Jira."""


class InvalidSecretsError(JiraReadonlyServiceError):
    """Некорректные секреты Jira."""


class SavedFilterNotFoundError(JiraReadonlyServiceError):
    """Не найден именованный JQL-фильтр."""

    def __init__(self, filter_name: str) -> None:
        super().__init__(f"Не найден сохранённый фильтр Jira: {filter_name}")
