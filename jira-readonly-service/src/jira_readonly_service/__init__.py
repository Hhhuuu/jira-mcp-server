"""Read-only сервис поверх Jira REST API."""

from .config import AppConfig, JiraAppConfig, load_app_config
from .dto import JiraCurrentUserResult, JiraIssueResult
from .exceptions import (
    ConfigFileNotFoundError,
    InvalidConfigError,
    InvalidSecretsError,
    JiraReadonlyServiceError,
    SecretsFileNotFoundError,
)
from .secrets import JiraSecrets, load_secrets
from .service import (
    JiraReadonlyService,
    format_current_user,
    format_issue,
    normalize_issue_ref,
    simplify_current_user,
    simplify_issue,
)

__all__ = [
    "AppConfig",
    "ConfigFileNotFoundError",
    "format_current_user",
    "InvalidConfigError",
    "InvalidSecretsError",
    "JiraCurrentUserResult",
    "JiraAppConfig",
    "JiraIssueResult",
    "JiraReadonlyService",
    "JiraReadonlyServiceError",
    "JiraSecrets",
    "SecretsFileNotFoundError",
    "format_issue",
    "load_app_config",
    "load_secrets",
    "normalize_issue_ref",
    "simplify_current_user",
    "simplify_issue",
]
