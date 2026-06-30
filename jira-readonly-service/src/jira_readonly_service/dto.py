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
