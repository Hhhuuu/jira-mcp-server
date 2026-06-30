"""DTO write-сервиса Jira."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JiraIssueTypeOption(BaseModel):
    """Доступный issue type для проекта."""

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    subtask: Optional[bool] = None


class JiraCreateIssueTypesResult(BaseModel):
    """Результат получения доступных issue types."""

    project_key: str
    issue_types: List[JiraIssueTypeOption]
    text: str


class JiraCreateFieldsResult(BaseModel):
    """Результат получения create field metadata."""

    project_key: str
    issue_type_id: str
    issue_type_name: Optional[str] = None
    fields: List[Dict[str, Any]]
    text: str


class JiraIssueMutationResult(BaseModel):
    """Результат create/update операции над issue."""

    operation: str
    issue_id: Optional[str] = None
    issue_key: Optional[str] = None
    issue_ref: Optional[str] = None
    url: Optional[str] = None
    changed_fields: List[str] = Field(default_factory=list)
    text: str


class JiraCommentMutationResult(BaseModel):
    """Результат create/update comment."""

    operation: str
    issue_ref: str
    comment_id: str
    text: str
