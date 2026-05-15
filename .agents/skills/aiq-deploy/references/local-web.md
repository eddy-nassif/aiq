# Local Web Deployment

Use this path for quick local development without Docker Compose when the user wants the browser UI.

For backend-only Agent Skill use, read `skill-backend.md` instead.

## Prerequisites

```bash
python3 --version
test -d .venv && echo "venv=present" || echo "venv=missing"
node --version 2>/dev/null || echo "node=missing"
npm --version 2>/dev/null || echo "npm=missing"
```

If `.venv` is missing, use the repository's documented setup flow before starting services. Ask before installing dependencies.

## Start

```bash
./scripts/start_e2e.sh --config_file configs/config_web_default_llamaindex.yml
```

The default local web path starts:

- backend: `http://localhost:8000`
- frontend: `http://localhost:3000`

## Verify

After startup, read `validation.md` and run the basic validation checks.
