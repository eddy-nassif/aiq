# Basic Validation

These checks confirm the deployed AI-Q system is reachable and minimally usable. They are not report-quality evaluation.

## Determine Server URL

Default:

```bash
PORT="${PORT:-8000}"
AIQ_SERVER_URL="${AIQ_SERVER_URL:-http://localhost:$PORT}"
echo "AIQ_SERVER_URL=$AIQ_SERVER_URL"
```

If the user configured a custom `PORT` or external host, use that URL.

## Backend API

```bash
curl -sf "$AIQ_SERVER_URL/health" >/dev/null && echo "backend=healthy"
```

If `/health` is unavailable, try `/v1/health` before failing:

```bash
curl -sf "$AIQ_SERVER_URL/v1/health" >/dev/null && echo "backend=healthy"
```

## UI When Applicable

Run this only for deployment modes that intentionally start the browser UI:

```bash
curl -sf "http://localhost:${FRONTEND_PORT:-3000}" >/dev/null && echo "frontend=reachable"
```

## Async Agent API

Use the installed `aiq-research` helper from the skill checkout when available:

```bash
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py health
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py agents
```

## Shallow End-To-End Check

Run a shallow `/chat` check when required model/search credentials are present. If credentials are missing, report that deploy validation reached infrastructure/API readiness but could not prove model-backed response generation.

```bash
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py chat "Briefly confirm AI-Q is responding."
```

Do not run deep research as part of basic deploy validation. Deep research belongs to `aiq-research` when requested, and broader research-system validation belongs to the future `aiq-evaluation` skill.

## Handoff

When validation passes, tell the user:

- backend URL
- frontend URL when applicable, or that the UI was intentionally not started
- whether `aiq-research` can use its default `AIQ_SERVER_URL`
- the exact `export AIQ_SERVER_URL=...` command when not using the default backend URL
