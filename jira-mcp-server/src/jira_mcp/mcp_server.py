"""MCP-сервер для read-only Jira сценариев."""

from __future__ import annotations

import os

from jira_readonly_service import JiraReadonlyService
from mcp.server.fastmcp import FastMCP

from .runtime import load_runtime_service, resolve_config_path, resolve_secrets_path

mcp = FastMCP(
    name="jira-readonly",
    instructions="Инструменты для безопасного read-only чтения задач Jira.",
    host=os.getenv("JIRA_MCP_HOST", "127.0.0.1"),
    port=int(os.getenv("JIRA_MCP_PORT", "3001")),
)


@mcp.tool(name="show_runtime_config", description="Показать пути к конфигу и секретам Jira.")
def show_runtime_config() -> dict:
    return {
        "config_path": str(resolve_config_path()),
        "secrets_path": str(resolve_secrets_path()),
    }


@mcp.tool(
    name="get_current_user",
    description="Проверить подключение к Jira и вернуть текущего пользователя, под которым выполнена авторизация.",
)
def get_current_user() -> dict:
    service: JiraReadonlyService = load_runtime_service()
    result = service.get_current_user()
    return result.model_dump(mode="json")


@mcp.tool(
    name="get_jira_issue",
    description="Прочитать информацию о Jira issue по ключу, id или Jira URL. Инструмент только для чтения.",
)
def get_jira_issue(issue_key: str, include_comments: bool = False, max_comments: int = 5) -> dict:
    service: JiraReadonlyService = load_runtime_service()
    result = service.get_jira_issue(
        issue_key,
        include_comments=include_comments,
        max_comments=max_comments,
    )
    return result.model_dump(mode="json")


def main() -> None:
    mcp.run(transport="stdio")
