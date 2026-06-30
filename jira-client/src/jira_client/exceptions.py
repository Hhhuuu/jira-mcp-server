"""Исключения Jira REST API клиента."""


class JiraClientError(Exception):
    """Базовое исключение клиента Jira."""


class JiraAuthenticationError(JiraClientError):
    """Ошибка авторизации в Jira."""


class JiraRequestError(JiraClientError):
    """Ошибка REST-запроса к Jira."""


class JiraIssueNotFoundError(JiraClientError):
    """Задача Jira не найдена."""
