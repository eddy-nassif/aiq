# Docker Compose Deployment

Use this as the default durable local deployment path for external users.

For Agent Skill backend use, start only `aiq-agent`; Docker Compose will also start required dependencies such as PostgreSQL. Start the `frontend` service only when the user asks for the browser UI.

## Prerequisites

```bash
docker --version
docker compose version
docker info >/dev/null
for port in 3000 8000 5432; do
  if lsof -nP -iTCP:$port -sTCP:LISTEN >/dev/null 2>&1; then
    echo "port $port is already in use"
  else
    echo "port $port is free"
  fi
done
```

If port `8000` is already in use, set `PORT=8100` or another free port in `deploy/.env` before starting Compose.

## Start For Agent Skill Backend

```bash
cd deploy/compose
BUILD_TARGET=release docker compose --env-file ../.env -f docker-compose.yaml config --quiet
BUILD_TARGET=release docker compose --env-file ../.env -f docker-compose.yaml up -d --build aiq-agent
```

Use pre-built images only when the user asks for registry images or faster startup:

```bash
cd deploy/compose
docker compose --env-file ../.env -f docker-compose.yaml up -d aiq-agent
```

The release build target excludes the CLI and debug UI. Keep this path backend-only unless the user asks for the browser UI.

## Start Full Browser UI

```bash
cd deploy/compose
docker compose --env-file ../.env -f docker-compose.yaml config --quiet
docker compose --env-file ../.env -f docker-compose.yaml up -d --build
```

Use pre-built images only when the user asks for registry images or faster startup:

```bash
cd deploy/compose
docker compose --env-file ../.env -f docker-compose.yaml up -d
```

## Runtime Checks

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E 'aiq-agent|aiq-blueprint-ui|aiq-postgres'
docker exec aiq-postgres pg_isready -U aiq -d aiq_jobs
docker exec aiq-postgres pg_isready -U aiq -d aiq_checkpoints
```

After startup, read `validation.md` and run the basic validation checks.
