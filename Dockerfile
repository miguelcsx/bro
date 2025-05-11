# Dockerfile para backend FastAPI + MCP
FROM python:3.11-slim

RUN apt-get update && apt-get install -y build-essential curl git

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY src ./src
COPY images ./images
COPY response.txt ./
COPY .env ./

EXPOSE 8888

CMD ["sh", "-c", "poetry run python -m src.main & poetry run python -m src.mcp.main & tail -f /dev/null"] 