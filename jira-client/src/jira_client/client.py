"""REST-клиент для работы с Jira."""

from __future__ import annotations

from dataclasses import dataclass
import base64
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx

from .exceptions import (
    JiraAuthenticationError,
    JiraIssueNotFoundError,
    JiraRequestError,
)
from .models import JiraErrorResponse, JiraIssueResponse, JiraProjectRef, JiraSearchResponse, JiraUserRef

DEFAULT_FIELDS = ",".join(
    [
        "summary",
        "status",
        "assignee",
        "reporter",
        "priority",
        "issuetype",
        "project",
        "created",
        "updated",
        "description",
        "labels",
        "components",
        "fixVersions",
        "parent",
        "duedate",
        "resolution",
    ]
)


@dataclass(frozen=True)
class JiraClientConfig:
    """
    Конфигурация Jira REST API клиента.

    Attributes:
        base_url: Базовый URL Jira.
        api_version: Версия REST API.
        deployment: Тип развертывания. Сейчас в основном влияет на семантику конфигурации.
        auth_type: `basic` или `bearer`.
        username: Логин или email для basic auth.
        api_token: API token для basic auth.
        bearer_token: OAuth bearer token.
        cloud_id: Cloud ID, если bearer auth идёт через `api.atlassian.com`.
        verify_ssl: Проверять ли SSL.
        timeout_seconds: Таймаут HTTP-запросов.
    """

    base_url: str
    api_version: str = "3"
    deployment: str = "cloud"
    auth_type: str = "basic"
    username: Optional[str] = None
    api_token: Optional[str] = None
    bearer_token: Optional[str] = None
    cloud_id: Optional[str] = None
    verify_ssl: bool = True
    timeout_seconds: float = 120.0


class JiraClient:
    """Клиент Jira REST API."""

    def __init__(self, config: JiraClientConfig) -> None:
        self._config = config
        self._api_base_url = self._build_api_base_url()
        self._client = httpx.Client(
            base_url=self._api_base_url,
            headers=self._build_headers(),
            verify=config.verify_ssl,
            timeout=config.timeout_seconds,
        )

    def get_issue(
        self,
        issue_key: str,
        *,
        include_comments: bool = False,
    ) -> JiraIssueResponse:
        """
        Получить задачу Jira по ключу или id.
        """

        fields = DEFAULT_FIELDS
        if include_comments:
            fields = f"{fields},comment"

        params: Dict[str, str] = {
            "fields": fields,
            "expand": "renderedFields,names",
        }
        if include_comments:
            params["fieldsByKeys"] = "true"

        response = self._request(
            "GET",
            f"/rest/api/{self._config.api_version}/issue/{quote(issue_key, safe='')}",
            params=params,
        )
        return JiraIssueResponse.model_validate(response.json())

    def get_current_user(self) -> JiraUserRef:
        """
        Получить текущего пользователя, под которым выполнена авторизация в Jira.
        """

        response = self._request(
            "GET",
            f"/rest/api/{self._config.api_version}/myself",
        )
        return JiraUserRef.model_validate(response.json())

    def get_project(self, project_key: str) -> JiraProjectRef:
        """
        Получить проект Jira по ключу.
        """

        response = self._request(
            "GET",
            f"/rest/api/{self._config.api_version}/project/{quote(project_key, safe='')}",
        )
        return JiraProjectRef.model_validate(response.json())

    def search_issues(
        self,
        jql: str,
        *,
        max_results: int = 20,
        start_at: int = 0,
    ) -> JiraSearchResponse:
        """
        Выполнить JQL поиск задач.
        """

        params: Dict[str, Any] = {
            "jql": jql,
            "fields": DEFAULT_FIELDS,
            "expand": "renderedFields,names",
            "maxResults": max_results,
            "startAt": start_at,
            "fieldsByKeys": "true",
        }

        search_path = (
            f"/rest/api/{self._config.api_version}/search/jql"
            if self._config.deployment == "cloud"
            else f"/rest/api/{self._config.api_version}/search"
        )

        response = self._request("GET", search_path, params=params)
        return JiraSearchResponse.model_validate(response.json())

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "JiraClient":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise JiraRequestError(f"Ошибка HTTP при обращении к Jira: {exc}") from exc

        if response.status_code == 401:
            raise JiraAuthenticationError("Авторизация в Jira неуспешна. Проверьте учетные данные.")
        if response.status_code == 404:
            raise JiraIssueNotFoundError("Задача Jira не найдена.")
        if response.status_code >= 400:
            raise JiraRequestError(self._build_error_message(response))
        return response

    def _build_api_base_url(self) -> str:
        base_url = self._config.base_url.rstrip("/")
        if self._config.auth_type == "bearer" and self._config.cloud_id:
            return f"https://api.atlassian.com/ex/jira/{self._config.cloud_id}"
        return base_url

    def _build_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._config.auth_type == "bearer":
            if not self._config.bearer_token:
                raise ValueError("Для bearer auth нужен bearer_token.")
            headers["Authorization"] = f"Bearer {self._config.bearer_token}"
            return headers

        if not self._config.username or not self._config.api_token:
            raise ValueError("Для basic auth нужны username и api_token.")
        token = base64.b64encode(
            f"{self._config.username}:{self._config.api_token}".encode("utf-8")
        ).decode("ascii")
        headers["Authorization"] = f"Basic {token}"
        return headers

    @staticmethod
    def _build_error_message(response: httpx.Response) -> str:
        detail = ""
        try:
            payload = JiraErrorResponse.model_validate(response.json())
            if payload.error_messages:
                detail = "; ".join(payload.error_messages)
            elif payload.message:
                detail = payload.message
        except Exception:
            detail = response.text

        if detail:
            return f"Jira вернула ошибку {response.status_code}: {detail}"
        return f"Jira вернула ошибку {response.status_code}: {response.reason_phrase}"
