FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY jira-client /app/jira-client
COPY jira-readonly-service /app/jira-readonly-service
COPY jira-write-service /app/jira-write-service
COPY jira-mcp-server /app/jira-mcp-server
COPY config /app/config
COPY secrets /app/secrets
COPY .mcp.json /app/.mcp.json
COPY EXTERNAL_CONSUMERS.md /app/EXTERNAL_CONSUMERS.md
COPY README.md /app/README.md
COPY LOCAL_ENVIRONMENTS.md /app/LOCAL_ENVIRONMENTS.md

RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir \
        -e /app/jira-client \
        -e /app/jira-readonly-service \
        -e /app/jira-write-service \
        -e /app/jira-mcp-server

ENV JIRA_CONFIG_PATH=/app/config/app.yaml
ENV JIRA_SECRETS_PATH=/app/secrets/jira.yaml
ENV JIRA_RUNTIME_MODE=http-api
ENV JIRA_HTTP_HOST=0.0.0.0
ENV JIRA_HTTP_PORT=8000
ENV JIRA_MCP_HOST=0.0.0.0
ENV JIRA_MCP_PORT=8000

EXPOSE 8000

CMD ["python", "-m", "jira_mcp.launch"]
