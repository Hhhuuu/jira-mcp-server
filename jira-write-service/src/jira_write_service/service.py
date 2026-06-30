"""Write use case слой для Jira."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from jira_client import JiraClient, JiraClientConfig, JiraCreateFieldsResponse, JiraCreateIssueTypesResponse
from jira_readonly_service import AppConfig, JiraSecrets

from .markdown_adf import markdown_to_adf
from .dto import (
    JiraCommentMutationResult,
    JiraCreateFieldsResult,
    JiraCreateIssueTypesResult,
    JiraIssueMutationResult,
    JiraIssueTypeOption,
)


class JiraWriteService:
    """Write use case слой для Jira."""

    def __init__(
        self,
        client: JiraClient,
        *,
        base_url: str,
        deployment: str,
        project_root: Path,
        field_aliases: Dict[str, str],
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._deployment = deployment
        self._project_root = project_root
        self._field_aliases = dict(field_aliases)

    @classmethod
    def from_config(
        cls,
        app_config: AppConfig,
        secrets: JiraSecrets,
        *,
        project_root: Path | None = None,
    ) -> "JiraWriteService":
        client = JiraClient(
            JiraClientConfig(
                base_url=app_config.jira.base_url,
                api_version=app_config.jira.api_version,
                deployment=app_config.jira.deployment,
                auth_type=secrets.auth_type,
                username=secrets.username,
                api_token=secrets.api_token,
                bearer_token=secrets.bearer_token,
                cloud_id=secrets.cloud_id,
                verify_ssl=app_config.jira.verify_ssl,
            )
        )
        return cls(
            client,
            base_url=app_config.jira.base_url,
            deployment=app_config.jira.deployment,
            project_root=project_root or Path.cwd(),
            field_aliases=app_config.jira.field_aliases,
        )

    def get_create_issue_types(self, project_key: str) -> JiraCreateIssueTypesResult:
        response = self._client.get_create_issue_types(project_key)
        issue_types = [
            JiraIssueTypeOption(
                id=item.id,
                name=item.name,
                description=item.description,
                subtask=item.subtask,
            )
            for item in response.issue_types
        ]
        return JiraCreateIssueTypesResult(
            project_key=project_key,
            issue_types=issue_types,
            text=format_issue_types(project_key, issue_types),
        )

    def get_create_issue_fields(self, project_key: str, issue_type: str) -> JiraCreateFieldsResult:
        issue_type_id, issue_type_name = self._resolve_issue_type(project_key, issue_type)
        response = self._client.get_create_issue_fields(project_key, issue_type_id)
        fields = [
            {
                "key": field.key,
                "name": field.name,
                "required": field.required,
                "hasDefaultValue": field.has_default_value,
                "schema": field.field_schema.model_dump(mode="json") if field.field_schema else None,
                "allowedValuesCount": len(field.allowed_values or []),
            }
            for field in response.fields
        ]
        return JiraCreateFieldsResult(
            project_key=project_key,
            issue_type_id=issue_type_id,
            issue_type_name=issue_type_name,
            fields=fields,
            text=format_create_fields(project_key, issue_type_name or issue_type_id, fields),
        )

    def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str,
        *,
        description: Optional[str] = None,
        description_markdown: Optional[str] = None,
        description_markdown_file: Optional[str] = None,
        labels: Optional[Sequence[str]] = None,
        parent_issue_key: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
        fields: Optional[Dict[str, Any]] = None,
    ) -> JiraIssueMutationResult:
        issue_type_id, issue_type_name = self._resolve_issue_type(project_key, issue_type)
        payload_fields: Dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"id": issue_type_id},
        }

        description_value = self._resolve_description_value(
            description=description,
            description_markdown=description_markdown,
            description_markdown_file=description_markdown_file,
        )
        if description_value is not None:
            payload_fields["description"] = description_value
        if labels:
            payload_fields["labels"] = list(labels)
        if parent_issue_key:
            payload_fields["parent"] = {"key": parent_issue_key}
        if custom_fields:
            payload_fields.update(self._apply_field_aliases(custom_fields))
        if fields:
            payload_fields.update(self._apply_field_aliases(fields))

        created = self._client.create_issue(payload_fields)
        issue_url = build_issue_url(self._base_url, created.key)
        changed_fields = sorted(payload_fields.keys())
        return JiraIssueMutationResult(
            operation="create_issue",
            issue_id=created.id,
            issue_key=created.key,
            url=issue_url,
            changed_fields=changed_fields,
            text=(
                f"Создана задача {created.key}: {summary}\n"
                f"Project: {project_key}\n"
                f"Issue type: {issue_type_name or issue_type_id}\n"
                f"URL: {issue_url}"
            ),
        )

    def update_issue_description(
        self,
        issue_ref: str,
        *,
        description: Optional[str] = None,
        description_markdown: Optional[str] = None,
        description_markdown_file: Optional[str] = None,
    ) -> JiraIssueMutationResult:
        description_value = self._resolve_description_value(
            description=description,
            description_markdown=description_markdown,
            description_markdown_file=description_markdown_file,
        )
        self._client.edit_issue(
            issue_ref,
            fields={"description": description_value},
        )
        return JiraIssueMutationResult(
            operation="update_description",
            issue_ref=issue_ref,
            changed_fields=["description"],
            text=f"Описание задачи {issue_ref} обновлено.",
        )

    def update_issue_fields(
        self,
        issue_ref: str,
        *,
        fields: Optional[Dict[str, Any]] = None,
        custom_fields: Optional[Dict[str, Any]] = None,
    ) -> JiraIssueMutationResult:
        merged_fields: Dict[str, Any] = {}
        if fields:
            merged_fields.update(self._apply_field_aliases(fields))
        if custom_fields:
            merged_fields.update(self._apply_field_aliases(custom_fields))
        self._client.edit_issue(issue_ref, fields=merged_fields)
        return JiraIssueMutationResult(
            operation="update_fields",
            issue_ref=issue_ref,
            changed_fields=sorted(merged_fields.keys()),
            text=f"Поля задачи {issue_ref} обновлены: {', '.join(sorted(merged_fields.keys())) or 'нет изменений'}.",
        )

    def update_issue_labels(
        self,
        issue_ref: str,
        *,
        add_labels: Optional[Sequence[str]] = None,
        remove_labels: Optional[Sequence[str]] = None,
        set_labels: Optional[Sequence[str]] = None,
    ) -> JiraIssueMutationResult:
        if set_labels is not None:
            self._client.edit_issue(issue_ref, fields={"labels": list(set_labels)})
            changed = ["labels"]
            text = f"Labels задачи {issue_ref} заменены: {', '.join(set_labels) if set_labels else 'пусто'}."
            return JiraIssueMutationResult(
                operation="set_labels",
                issue_ref=issue_ref,
                changed_fields=changed,
                text=text,
            )

        update_ops: List[Dict[str, str]] = []
        for label in add_labels or []:
            update_ops.append({"add": label})
        for label in remove_labels or []:
            update_ops.append({"remove": label})

        self._client.edit_issue(issue_ref, update={"labels": update_ops})
        parts: List[str] = []
        if add_labels:
            parts.append(f"добавлены: {', '.join(add_labels)}")
        if remove_labels:
            parts.append(f"удалены: {', '.join(remove_labels)}")
        return JiraIssueMutationResult(
            operation="update_labels",
            issue_ref=issue_ref,
            changed_fields=["labels"],
            text=f"Labels задачи {issue_ref} обновлены ({'; '.join(parts) or 'без изменений'}).",
        )

    def add_comment(self, issue_ref: str, comment: str) -> JiraCommentMutationResult:
        created = self._client.add_comment(
            issue_ref,
            build_rich_text_value(comment, deployment=self._deployment),
        )
        return JiraCommentMutationResult(
            operation="add_comment",
            issue_ref=issue_ref,
            comment_id=created.id,
            text=f"Комментарий {created.id} добавлен в задачу {issue_ref}.",
        )

    def update_comment(self, issue_ref: str, comment_id: str, comment: str) -> JiraCommentMutationResult:
        updated = self._client.update_comment(
            issue_ref,
            comment_id,
            build_rich_text_value(comment, deployment=self._deployment),
        )
        return JiraCommentMutationResult(
            operation="update_comment",
            issue_ref=issue_ref,
            comment_id=updated.id,
            text=f"Комментарий {updated.id} в задаче {issue_ref} обновлён.",
        )

    def _resolve_issue_type(self, project_key: str, issue_type: str) -> tuple[str, Optional[str]]:
        issue_types = self._client.get_create_issue_types(project_key).issue_types
        requested = issue_type.strip()
        if requested.isdigit():
            for candidate in issue_types:
                if candidate.id == requested:
                    return requested, candidate.name
            return requested, None

        lowered = requested.casefold()
        for candidate in issue_types:
            if candidate.name and candidate.name.casefold() == lowered:
                return candidate.id or requested, candidate.name

        raise ValueError(
            f"Не удалось найти issue type '{issue_type}' для проекта {project_key}. "
            f"Сначала вызови get_create_issue_types."
        )

    def _resolve_description_value(
        self,
        *,
        description: Optional[str],
        description_markdown: Optional[str],
        description_markdown_file: Optional[str],
    ) -> Any:
        if description_markdown_file:
            markdown_path = self._resolve_local_path(description_markdown_file)
            markdown_text = markdown_path.read_text(encoding="utf-8")
            return markdown_to_adf(markdown_text) if self._deployment == "cloud" else markdown_text
        if description_markdown:
            return markdown_to_adf(description_markdown) if self._deployment == "cloud" else description_markdown
        if description is not None:
            return build_rich_text_value(description, deployment=self._deployment)
        raise ValueError("Нужно передать description, description_markdown или description_markdown_file.")

    def _resolve_local_path(self, path_value: str) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        candidate = self._project_root / path
        if candidate.exists():
            return candidate
        return Path.cwd() / path

    def _apply_field_aliases(self, values: Dict[str, Any]) -> Dict[str, Any]:
        resolved: Dict[str, Any] = {}
        for key, value in values.items():
            resolved_key = self._field_aliases.get(key, key)
            resolved[resolved_key] = value
        return resolved


def build_rich_text_value(value: Any, *, deployment: str) -> Any:
    if isinstance(value, dict):
        return value
    if deployment == "cloud":
        return {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": str(value),
                        }
                    ],
                }
            ],
        }
    return str(value)


def build_issue_url(base_url: str, issue_key: str) -> str:
    return f"{base_url.rstrip('/')}/browse/{issue_key}"


def format_issue_types(project_key: str, issue_types: Sequence[JiraIssueTypeOption]) -> str:
    lines = [f"Project: {project_key}", "Available issue types:", ""]
    for issue_type in issue_types:
        lines.append(
            f"- {issue_type.id or '?'}: {issue_type.name or 'Unknown'}"
            + (" (subtask)" if issue_type.subtask else "")
        )
    return "\n".join(lines)


def format_create_fields(project_key: str, issue_type_name: str, fields: Sequence[Dict[str, Any]]) -> str:
    lines = [f"Project: {project_key}", f"Issue type: {issue_type_name}", "Create fields:", ""]
    for field in fields:
        required = "required" if field.get("required") else "optional"
        lines.append(f"- {field.get('key')}: {field.get('name')} [{required}]")
    return "\n".join(lines)
