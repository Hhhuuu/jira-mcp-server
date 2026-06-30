"""Модели Jira REST API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class JiraModel(BaseModel):
    """Базовая модель Jira API с игнорированием лишних полей."""

    model_config = ConfigDict(extra="ignore")


class JiraUserRef(JiraModel):
    """Пользователь Jira."""

    account_id: Optional[str] = Field(default=None, alias="accountId")
    display_name: Optional[str] = Field(default=None, alias="displayName")
    email_address: Optional[str] = Field(default=None, alias="emailAddress")
    active: Optional[bool] = None


class JiraNamedValue(JiraModel):
    """Простое Jira-поле с `name`."""

    id: Optional[str] = None
    name: Optional[str] = None


class JiraProjectRef(JiraModel):
    """Ссылка на проект Jira."""

    id: Optional[str] = None
    key: Optional[str] = None
    name: Optional[str] = None
    project_type_key: Optional[str] = Field(default=None, alias="projectTypeKey")
    simplified: Optional[bool] = None


class JiraParentFields(JiraModel):
    """Подмножество полей родительской задачи."""

    summary: Optional[str] = None


class JiraParentRef(JiraModel):
    """Ссылка на родительскую задачу."""

    id: Optional[str] = None
    key: Optional[str] = None
    fields: Optional[JiraParentFields] = None


class JiraCommentBody(JiraModel):
    """ADF или plain текст тела комментария."""

    type: Optional[str] = None
    content: Optional[List[Dict[str, Any]]] = None


class JiraComment(JiraModel):
    """Комментарий Jira."""

    id: str
    author: Optional[JiraUserRef] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    body: Optional[Any] = None


class JiraCommentContainer(JiraModel):
    """Контейнер комментариев Jira."""

    comments: List[JiraComment] = Field(default_factory=list)


class JiraFields(JiraModel):
    """Основные поля Jira issue."""

    summary: Optional[str] = None
    status: Optional[JiraNamedValue] = None
    assignee: Optional[JiraUserRef] = None
    reporter: Optional[JiraUserRef] = None
    priority: Optional[JiraNamedValue] = None
    issuetype: Optional[JiraNamedValue] = None
    project: Optional[JiraProjectRef] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    description: Optional[Any] = None
    labels: List[str] = Field(default_factory=list)
    components: List[JiraNamedValue] = Field(default_factory=list)
    fix_versions: List[JiraNamedValue] = Field(default_factory=list, alias="fixVersions")
    parent: Optional[JiraParentRef] = None
    duedate: Optional[str] = None
    resolution: Optional[JiraNamedValue] = None
    comment: Optional[JiraCommentContainer] = None


class JiraIssueResponse(JiraModel):
    """Полный ответ Jira по задаче."""

    id: str
    key: str
    self: str
    fields: JiraFields = Field(default_factory=JiraFields)


class JiraIssueTypeRef(JiraModel):
    """Тип задачи Jira."""

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    subtask: Optional[bool] = None


class JiraCreateIssueTypesResponse(JiraModel):
    """Список доступных issue types для создания в проекте."""

    issue_types: List[JiraIssueTypeRef] = Field(default_factory=list, alias="issueTypes")
    total: int = 0
    start_at: int = Field(default=0, alias="startAt")
    max_results: int = Field(default=0, alias="maxResults")


class JiraFieldSchema(JiraModel):
    """Схема Jira field metadata."""

    type: Optional[str] = None
    system: Optional[str] = None
    custom: Optional[str] = None
    custom_id: Optional[int] = Field(default=None, alias="customId")


class JiraFieldMetadata(JiraModel):
    """Метаданные поля для create/edit."""

    key: Optional[str] = None
    name: Optional[str] = None
    required: bool = False
    has_default_value: bool = Field(default=False, alias="hasDefaultValue")
    field_schema: Optional[JiraFieldSchema] = Field(default=None, alias="schema")
    allowed_values: List[Any] = Field(default_factory=list, alias="allowedValues")


class JiraCreateFieldsResponse(JiraModel):
    """Список полей, доступных для создания задачи."""

    fields: List[JiraFieldMetadata] = Field(default_factory=list)
    total: int = 0
    start_at: int = Field(default=0, alias="startAt")
    max_results: int = Field(default=0, alias="maxResults")


class JiraCommentResponse(JiraModel):
    """Комментарий Jira после создания или обновления."""

    id: str
    self: Optional[str] = None
    body: Optional[Any] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    author: Optional[JiraUserRef] = None


class JiraCreateIssueResponse(JiraModel):
    """Ответ Jira на создание задачи."""

    id: str
    key: str
    self: str


class JiraSearchResponse(JiraModel):
    """Ответ Jira search API."""

    issues: List[JiraIssueResponse] = Field(default_factory=list)
    total: int = 0
    start_at: int = Field(default=0, alias="startAt")
    max_results: int = Field(default=0, alias="maxResults")


class JiraErrorResponse(JiraModel):
    """Ошибка Jira REST API."""

    error_messages: List[str] = Field(default_factory=list, alias="errorMessages")
    message: Optional[str] = None
