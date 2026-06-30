"""Read-only сервис поверх Jira REST API."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

from jira_client import JiraClient, JiraClientConfig, JiraIssueResponse, JiraUserRef

from .config import AppConfig
from .dto import JiraCurrentUserResult, JiraIssueResult
from .secrets import JiraSecrets


class JiraReadonlyService:
    """Read-only use case слой для Jira."""

    def __init__(self, client: JiraClient) -> None:
        self._client = client

    @classmethod
    def from_config(cls, app_config: AppConfig, secrets: JiraSecrets) -> "JiraReadonlyService":
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
        return cls(client)

    def get_jira_issue(
        self,
        issue_key: str,
        *,
        include_comments: bool = False,
        max_comments: int = 5,
    ) -> JiraIssueResult:
        issue_ref = normalize_issue_ref(issue_key)
        response = self._client.get_issue(issue_ref, include_comments=include_comments)
        simplified = simplify_issue(response, include_comments=include_comments, max_comments=max_comments)
        return JiraIssueResult(
            issue=simplified,
            text=format_issue(simplified),
            issue_ref=issue_ref,
            include_comments=include_comments,
            max_comments=max_comments,
        )

    def get_current_user(self) -> JiraCurrentUserResult:
        response = self._client.get_current_user()
        simplified = simplify_current_user(response)
        return JiraCurrentUserResult(
            user=simplified,
            text=format_current_user(simplified),
        )


def normalize_issue_ref(value: str) -> str:
    """Нормализовать issue key/id или Jira URL."""

    raw_value = value.strip()
    try:
        parsed = urlparse(raw_value)
        if parsed.scheme and parsed.netloc:
            params = parse_qs(parsed.query)
            selected_issue = params.get("selectedIssue", [])
            if selected_issue and selected_issue[0].strip():
                return selected_issue[0].strip()

            match = re.search(r"/browse/([A-Z][A-Z0-9]+-\d+)\b", parsed.path, flags=re.IGNORECASE)
            if match:
                return match.group(1).upper()
    except Exception:
        return raw_value
    return raw_value


def simplify_issue(
    issue: JiraIssueResponse,
    *,
    include_comments: bool,
    max_comments: int,
) -> Dict[str, Any]:
    fields = issue.fields
    simplified: Dict[str, Any] = {
        "id": issue.id,
        "key": issue.key,
        "self": issue.self,
        "summary": fields.summary,
        "issueType": pick_name(fields.issuetype),
        "status": pick_name(fields.status),
        "priority": pick_name(fields.priority),
        "resolution": pick_name(fields.resolution),
        "project": {
            "key": fields.project.key if fields.project else None,
            "name": fields.project.name if fields.project else None,
        }
        if fields.project
        else None,
        "assignee": pick_user(fields.assignee),
        "reporter": pick_user(fields.reporter),
        "created": fields.created,
        "updated": fields.updated,
        "dueDate": fields.duedate,
        "labels": fields.labels or [],
        "components": [pick_name(item) for item in fields.components],
        "fixVersions": [pick_name(item) for item in fields.fix_versions],
        "parent": {
            "id": fields.parent.id,
            "key": fields.parent.key,
            "summary": fields.parent.fields.summary if fields.parent and fields.parent.fields else None,
        }
        if fields.parent
        else None,
        "description": adf_to_text(fields.description),
    }

    if include_comments:
        comments = fields.comment.comments if fields.comment else []
        simplified["comments"] = [
            {
                "id": comment.id,
                "author": pick_user(comment.author),
                "created": comment.created,
                "updated": comment.updated,
                "body": adf_to_text(comment.body),
            }
            for comment in comments[-max_comments:]
        ]
    return simplified


def simplify_current_user(user: JiraUserRef) -> Dict[str, Any]:
    return {
        "accountId": user.account_id,
        "displayName": user.display_name,
        "emailAddress": user.email_address,
        "active": user.active,
    }


def pick_name(value: Any) -> Optional[str]:
    return getattr(value, "name", None) if value else None


def pick_user(user: Any) -> Optional[Dict[str, Any]]:
    if not user:
        return None
    return {
        "accountId": user.account_id,
        "displayName": user.display_name,
        "emailAddress": user.email_address,
        "active": user.active,
    }


def adf_to_text(value: Any) -> Optional[str]:
    if not value:
        return None
    if isinstance(value, str):
        return strip_html(value)

    parts: List[str] = []
    visit_adf(value, parts)
    text = "".join(parts)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text or None


def visit_adf(node: Any, parts: List[str]) -> None:
    if not node or not isinstance(node, dict):
        return

    text = node.get("text")
    if isinstance(text, str):
        parts.append(text)

    if node.get("type") == "hardBreak":
        parts.append("\n")

    content = node.get("content")
    if isinstance(content, list):
        for child in content:
            visit_adf(child, parts)

    if node.get("type") in {"paragraph", "heading", "listItem", "bulletList", "orderedList", "blockquote"}:
        parts.append("\n")


def strip_html(value: str) -> str:
    normalized = (
        value.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("<br/>", "\n")
        .replace("<br />", "\n")
        .replace("<br>", "\n")
        .replace("</p>", "\n")
    )
    normalized = re.sub(r"<[^>]+>", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def format_issue(issue: Dict[str, Any]) -> str:
    lines = [
        f"{issue.get('key')}: {issue.get('summary') or 'No summary'}",
        f"Type: {issue.get('issueType') or 'Unknown'}",
        f"Status: {issue.get('status') or 'Unknown'}",
        f"Priority: {issue.get('priority') or 'None'}",
        f"Resolution: {issue.get('resolution') or 'Unresolved'}",
        f"Project: {issue.get('project', {}).get('key') if issue.get('project') else 'Unknown'}"
        + (
            f" - {issue.get('project', {}).get('name')}"
            if issue.get("project") and issue["project"].get("name")
            else ""
        ),
        f"Assignee: {issue.get('assignee', {}).get('displayName') if issue.get('assignee') else 'Unassigned'}",
        f"Reporter: {issue.get('reporter', {}).get('displayName') if issue.get('reporter') else 'Unknown'}",
        f"Created: {issue.get('created') or 'Unknown'}",
        f"Updated: {issue.get('updated') or 'Unknown'}",
        f"Due date: {issue.get('dueDate') or 'None'}",
        f"Labels: {', '.join(issue.get('labels', [])) if issue.get('labels') else 'None'}",
        f"Components: {', '.join(issue.get('components', [])) if issue.get('components') else 'None'}",
        f"Fix versions: {', '.join(issue.get('fixVersions', [])) if issue.get('fixVersions') else 'None'}",
    ]

    parent = issue.get("parent")
    if parent:
        lines.append(f"Parent: {parent.get('key')} - {parent.get('summary') or 'No summary'}")

    description = issue.get("description")
    if description:
        lines.extend(["", "Description:", description])

    comments = issue.get("comments")
    if comments:
        lines.extend(["", f"Latest comments: {len(comments)}"])
        for comment in comments:
            author = comment.get("author", {}).get("displayName") if comment.get("author") else "Unknown author"
            lines.extend(["", f"[{comment.get('created') or 'Unknown date'}] {author}", comment.get("body") or ""])

    return "\n".join(lines)


def format_current_user(user: Dict[str, Any]) -> str:
    lines = [
        f"Current user: {user.get('displayName') or 'Unknown'}",
        f"Account ID: {user.get('accountId') or 'Unknown'}",
        f"Email: {user.get('emailAddress') or 'Unavailable'}",
        f"Active: {user.get('active') if user.get('active') is not None else 'Unknown'}",
    ]
    return "\n".join(lines)
