"""Локальный HTTP API для ручной проверки read-only Jira логики."""

from __future__ import annotations

from typing import Dict

from fastapi import FastAPI, HTTPException
from jira_client import JiraAuthenticationError, JiraIssueNotFoundError, JiraRequestError
from jira_readonly_service import (
    ConfigFileNotFoundError,
    InvalidConfigError,
    InvalidSecretsError,
    JiraFilterService,
    SavedFilterNotFoundError,
    SecretsFileNotFoundError,
    load_app_config,
    save_app_config,
)

from .runtime import load_runtime_service, resolve_config_path, resolve_secrets_path

app = FastAPI(
    title="Jira Preview API",
    version="0.1.0",
    description="Локальный API для проверки read-only Jira сценариев.",
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/config")
def show_config() -> Dict[str, str | bool]:
    try:
        config = load_app_config(resolve_config_path())
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "config_path": str(resolve_config_path()),
        "secrets_path": str(resolve_secrets_path()),
        "base_url": config.jira.base_url,
        "api_version": config.jira.api_version,
        "deployment": config.jira.deployment,
        "verify_ssl": config.jira.verify_ssl,
    }


@app.get("/api/v1/me")
def get_current_user() -> dict:
    try:
        service = load_runtime_service()
        result = service.get_current_user()
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except JiraAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except JiraRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.model_dump(mode="json")


@app.get("/api/v1/project")
def get_project(project_key: str) -> dict:
    try:
        service = load_runtime_service()
        result = service.get_project(project_key)
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except JiraAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except JiraRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.model_dump(mode="json")


@app.get("/api/v1/issue")
def get_issue(issue_key: str, include_comments: bool = False, max_comments: int = 5) -> dict:
    try:
        service = load_runtime_service()
        result = service.get_jira_issue(
            issue_key,
            include_comments=include_comments,
            max_comments=max_comments,
        )
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except JiraAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except JiraIssueNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except JiraRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.model_dump(mode="json")


@app.get("/api/v1/search")
def search_issues(jql: str, max_results: int = 20, start_at: int = 0) -> dict:
    try:
        service = load_runtime_service()
        result = service.search_issues_by_jql(
            jql,
            max_results=max_results,
            start_at=start_at,
        )
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except JiraAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except JiraRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.model_dump(mode="json")


@app.get("/api/v1/filters")
def list_filters() -> dict:
    try:
        config = load_app_config(resolve_config_path())
        filters = JiraFilterService(config).list_saved_filters()
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"filters": [item.model_dump(mode="json") for item in filters]}


@app.post("/api/v1/filters")
def upsert_filter(
    filter_name: str,
    description: str | None = None,
    jql: str | None = None,
    jql_template: str | None = None,
    year_field: str = "created",
) -> dict:
    try:
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
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.model_dump(mode="json")


@app.delete("/api/v1/filters")
def delete_filter(filter_name: str) -> dict:
    try:
        config = load_app_config(resolve_config_path())
        filter_service = JiraFilterService(config)
        filter_service.delete_saved_filter(filter_name)
        save_app_config(resolve_config_path(), config)
    except SavedFilterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"deleted": filter_name}


@app.get("/api/v1/filters/search")
def search_by_saved_filter(filter_name: str, year: int | None = None, max_results: int = 20, start_at: int = 0) -> dict:
    try:
        config = load_app_config(resolve_config_path())
        filter_service = JiraFilterService(config)
        jql = filter_service.resolve_saved_filter_jql(filter_name, year=year)
        service = load_runtime_service()
        result = service.search_issues_by_jql(
            jql,
            max_results=max_results,
            start_at=start_at,
        )
    except SavedFilterNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ConfigFileNotFoundError, InvalidConfigError, InvalidSecretsError, SecretsFileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except JiraAuthenticationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except JiraRequestError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result.model_dump(mode="json")
