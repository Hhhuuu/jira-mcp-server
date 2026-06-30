"""MCP-сервер для read-only Jira сценариев."""

from __future__ import annotations

import os

from jira_readonly_service import JiraFilterService, JiraReadonlyService, load_app_config, save_app_config
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


@mcp.tool(
    name="get_jira_project",
    description="Прочитать информацию о Jira project по ключу.",
)
def get_jira_project(project_key: str) -> dict:
    service: JiraReadonlyService = load_runtime_service()
    result = service.get_project(project_key)
    return result.model_dump(mode="json")


@mcp.tool(
    name="search_jira_issues",
    description="Выполнить JQL-поиск задач Jira в read-only режиме.",
)
def search_jira_issues(jql: str, max_results: int = 20, start_at: int = 0) -> dict:
    service: JiraReadonlyService = load_runtime_service()
    result = service.search_issues_by_jql(
        jql,
        max_results=max_results,
        start_at=start_at,
    )
    return result.model_dump(mode="json")


@mcp.tool(
    name="list_saved_jql_filters",
    description="Показать локально сохранённые именованные JQL-фильтры из config/app.yaml.",
)
def list_saved_jql_filters() -> dict:
    config = load_app_config(resolve_config_path())
    filters = JiraFilterService(config).list_saved_filters()
    return {"filters": [item.model_dump(mode="json") for item in filters]}


@mcp.tool(
    name="save_jql_filter",
    description="Сохранить или обновить локальный именованный JQL-фильтр в config/app.yaml.",
)
def save_jql_filter(
    filter_name: str,
    description: str | None = None,
    jql: str | None = None,
    jql_template: str | None = None,
    year_field: str = "created",
) -> dict:
    config = load_app_config(resolve_config_path())
    filter_service = JiraFilterService(config)
    result = filter_service.upsert_saved_filter(
        filter_name,
        description=description,
        jql=jql,
        jql_template=jql_template,
        year_field=year_field,
    )
    save_app_config(resolve_config_path(), config)
    return result.model_dump(mode="json")


@mcp.tool(
    name="delete_jql_filter",
    description="Удалить локальный именованный JQL-фильтр из config/app.yaml.",
)
def delete_jql_filter(filter_name: str) -> dict:
    config = load_app_config(resolve_config_path())
    filter_service = JiraFilterService(config)
    filter_service.delete_saved_filter(filter_name)
    save_app_config(resolve_config_path(), config)
    return {"deleted": filter_name}


@mcp.tool(
    name="search_jira_by_saved_filter",
    description="Выполнить поиск задач по локально сохранённому именованному JQL-фильтру, при необходимости ограничив результаты по году.",
)
def search_jira_by_saved_filter(filter_name: str, year: int | None = None, max_results: int = 20, start_at: int = 0) -> dict:
    config = load_app_config(resolve_config_path())
    filter_service = JiraFilterService(config)
    jql = filter_service.resolve_saved_filter_jql(filter_name, year=year)
    service: JiraReadonlyService = load_runtime_service()
    result = service.search_issues_by_jql(
        jql,
        max_results=max_results,
        start_at=start_at,
    )
    return result.model_dump(mode="json")


def main() -> None:
    mcp.run(transport="stdio")
