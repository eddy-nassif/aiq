# Agent Skill Backend Deployment

Use this path when the user wants a local AI-Q backend for the `aiq-research` Agent Skill without starting the browser UI.

This mode starts only the API server. It does not start the Next.js UI, and it disables the optional debug console.

## Prerequisites

```bash
python3 --version
test -d .venv && echo "venv=present" || echo "venv=missing"
```

If `.venv` is missing, use the repository's documented setup flow before starting services. Ask before installing dependencies.

## Start

```bash
./scripts/start_as_skill.sh --config_file configs/config_web_default_llamaindex.yml --port 8000
```

The default Agent Skill backend path starts:

- backend API: `http://localhost:8000`
- skill handoff URL: `AIQ_SERVER_URL=http://localhost:8000`
- frontend UI: not started
- debug console: disabled

## Verify

After startup, read `validation.md` and run the basic backend and async-agent validation checks. Do not require the frontend check for this mode.
