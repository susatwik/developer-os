# Deployment Guide

Developer OS can be deployed with Docker locally or pushed to Render, Railway, or Fly.io with the same container image and environment variables.

## Prerequisites

1. Clone the repository.
2. Copy `.env.example` to `.env`.
3. Set any usernames, tokens, and runtime options you want to enable.
4. Make sure `data/` exists locally if you want tracker state persisted on the host.

## Local Docker Run

```bash
cp .env.example .env
docker compose up --build
```

Open:

- `http://localhost:8000/dashboard`
- `http://localhost:8000/health`
- `http://localhost:8000/version`

## Environment Variables

Required for live integrations:

- `DEVOS_GITHUB_USERNAME`
- `DEVOS_LEETCODE_USERNAME`

Optional:

- `DEVOS_GITHUB_TOKEN`
- `DEVOS_LEETCODE_SESSION_COOKIE`
- `DEVOS_HOST`
- `DEVOS_PORT`
- `WEB_CONCURRENCY`
- `DEVOS_LOG_LEVEL`
- `DEVOS_ACCESS_LOG`
- `DEVOS_ACCESS_LOG_FILE`
- `DEVOS_ERROR_LOG_FILE`

## Render

Use Render's Docker deployment flow:

1. Create a new Web Service from your GitHub repo.
2. Select `Docker` as the environment.
3. Set the service health check path to `/health`.
4. Add the environment variables from `.env.example` in the Render dashboard.
5. Leave the build/start commands empty if Render is building from the Dockerfile.
6. Deploy.

Recommended runtime values:

- Start command: `gunicorn -c gunicorn.conf.py developer_os.webapp:app`
- Health check path: `/health`

## Railway

Use Railway's Dockerfile deployment flow:

1. Create a new project and deploy from GitHub.
2. Let Railway detect the Dockerfile in the repository root.
3. Add the environment variables from `.env.example`.
4. Set the service port to `8000` if Railway asks for one.
5. Deploy the service.

Recommended runtime values:

- Start command: `gunicorn -c gunicorn.conf.py developer_os.webapp:app`
- Health check path: `/health`

## Fly.io

Use Fly.io's Dockerfile workflow:

```bash
fly launch --no-deploy
fly secrets set DEVOS_GITHUB_USERNAME=your-user
fly secrets set DEVOS_LEETCODE_USERNAME=your-user
fly deploy
```

Fly Launch detects the Dockerfile, creates `fly.toml`, and uses port `8080` by default when no port is declared. This app exposes port `8000`, so keep the generated `fly.toml` service port aligned with the Dockerfile if you customize it.

Recommended runtime values:

- Start command: `gunicorn -c gunicorn.conf.py developer_os.webapp:app`
- Health check path: `/health`

## Production Endpoints

- `/health` returns a JSON health payload.
- `/version` returns the application version.

## Reproducible Checklist

1. Copy `.env.example` to `.env`.
2. Fill in the environment variables you need.
3. Run `docker compose up --build`.
4. Confirm `/health` and `/version` respond.
5. Use the same Dockerfile and env variables for Render, Railway, or Fly.io.
