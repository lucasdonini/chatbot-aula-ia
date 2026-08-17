FROM node:24-alpine AS frontend

WORKDIR /app

COPY frontend/package*.json .
RUN npm ci

COPY frontend .
RUN npm run build

FROM python:3.14-slim-bookworm

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app app
COPY --from=frontend /app/dist ./frontend/dist

RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
