"""DTO read-only Jira сервиса."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JiraIssueResult(BaseModel):
    """Результат получения Jira issue."""

    issue: Dict[str, Any]
    text: str
    issue_ref: str
    include_comments: bool = False
    max_comments: int = 5


class JiraCurrentUserResult(BaseModel):
    """Результат проверки текущего пользователя Jira."""

    user: Dict[str, Any]
    text: str


class JiraProjectResult(BaseModel):
    """Результат получения Jira project."""

    project: Dict[str, Any]
    text: str


class JiraSearchResult(BaseModel):
    """Результат JQL-поиска."""

    jql: str
    total: int
    start_at: int = 0
    max_results: int = 20
    issues: List[Dict[str, Any]]
    text: str


class JiraSavedFilterResult(BaseModel):
    """Описание сохранённого фильтра."""

    name: str
    description: Optional[str] = None
    jql: Optional[str] = None
    jql_template: Optional[str] = None
    year_field: str = "created"
