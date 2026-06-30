"""MCP-сервер для read-only Jira сценариев."""

from __future__ import annotations

import os

from jira_readonly_service import JiraFilterService, JiraReadonlyService, load_app_config, save_app_config
from jira_write_service import JiraWriteService
from mcp.server.fastmcp import FastMCP

from .runtime import load_runtime_service, load_runtime_write_service, resolve_config_path, resolve_secrets_path

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


@mcp.tool(
    name="get_jira_create_issue_types",
    description="Показать доступные issue types для создания задачи в проекте Jira.",
)
def get_jira_create_issue_types(project_key: str) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.get_create_issue_types(project_key)
    return result.model_dump(mode="json")


@mcp.tool(
    name="get_jira_create_issue_fields",
    description="Показать поля, доступные для создания Jira issue в проекте и issue type.",
)
def get_jira_create_issue_fields(project_key: str, issue_type: str) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.get_create_issue_fields(project_key, issue_type)
    return result.model_dump(mode="json")


@mcp.tool(
    name="create_jira_issue",
    description="Создать Jira issue с заданным project, summary, issue type, labels и дополнительными полями.",
)
def create_jira_issue(
    project_key: str,
    summary: str,
    issue_type: str,
    description: str | None = None,
    labels: list[str] | None = None,
    parent_issue_key: str | None = None,
    custom_fields: dict | None = None,
    fields: dict | None = None,
) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.create_issue(
        project_key,
        summary,
        issue_type,
        description=description,
        labels=labels,
        parent_issue_key=parent_issue_key,
        custom_fields=custom_fields,
        fields=fields,
    )
    return result.model_dump(mode="json")


@mcp.tool(
    name="add_jira_comment",
    description="Добавить комментарий к Jira issue.",
)
def add_jira_comment(issue_ref: str, comment: str) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.add_comment(issue_ref, comment)
    return result.model_dump(mode="json")


@mcp.tool(
    name="update_jira_comment",
    description="Обновить существующий комментарий Jira.",
)
def update_jira_comment(issue_ref: str, comment_id: str, comment: str) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.update_comment(issue_ref, comment_id, comment)
    return result.model_dump(mode="json")


@mcp.tool(
    name="update_jira_description",
    description="Обновить описание Jira issue.",
)
def update_jira_description(issue_ref: str, description: str) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.update_issue_description(issue_ref, description)
    return result.model_dump(mode="json")


@mcp.tool(
    name="update_jira_labels",
    description="Добавить, удалить или заменить labels у Jira issue.",
)
def update_jira_labels(
    issue_ref: str,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    set_labels: list[str] | None = None,
) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.update_issue_labels(
        issue_ref,
        add_labels=add_labels,
        remove_labels=remove_labels,
        set_labels=set_labels,
    )
    return result.model_dump(mode="json")


@mcp.tool(
    name="update_jira_fields",
    description="Обновить произвольные поля Jira issue, включая customfield_*.",
)
def update_jira_fields(issue_ref: str, fields: dict | None = None, custom_fields: dict | None = None) -> dict:
    service: JiraWriteService = load_runtime_write_service()
    result = service.update_issue_fields(
        issue_ref,
        fields=fields,
        custom_fields=custom_fields,
    )
    return result.model_dump(mode="json")


def main() -> None:
    mcp.run(transport="stdio")
