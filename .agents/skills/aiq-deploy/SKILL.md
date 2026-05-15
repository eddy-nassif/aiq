---
name: aiq-deploy
description: Deploy, verify, troubleshoot, or stop a local or self-hosted NVIDIA AI-Q Blueprint server for external users. Use when asked to install AIQ, clone AIQ, start AI-Q, run the UI/backend, deploy with Docker Compose or Helm, check health, inspect logs, rebuild, stop services, or prepare a running AI-Q server for the aiq-research skill.
license: Apache-2.0
compatibility: Claude Code, OpenCode, Codex, and Agent Skills-compatible tools. Requires access to the AI-Q repository and the runtime selected by the user.
metadata:
  version: "2.1.0"
  github-url: "https://github.com/NVIDIA-AI-Blueprints/aiq"
  tags: "nvidia aiq blueprint deploy operations agent-skills"
allowed-tools: Read Bash
---

# AIQ Deploy Skill

Use this skill to get a local or self-hosted NVIDIA AI-Q Blueprint server running and verified for use by `aiq-research`.

This skill owns setup, deployment, operational checks, troubleshooting, and shutdown. It does not run deep research itself. After deployment is healthy, hand off the verified server URL to `aiq-research`.

## Operating Boundary

- Target external/open-source users of `NVIDIA-AI-Blueprints/aiq`.
- Do not assume access to hosted AIQ endpoints.
- Use `http://localhost:8000` unless the user chooses another local or self-hosted URL.

## Safety Rules

- Never print secret values. Check only whether required environment variables are set.
- Do not overwrite `deploy/.env` when it already exists.
- Ask before destructive cleanup such as deleting Docker volumes with `down -v`.
- Do not claim FRAG is ready unless both `RAG_SERVER_URL` and `RAG_INGEST_URL` are configured and reachable.
- Run verification commands yourself when possible.

## Intent Routing

Match the user request, then read the referenced file before acting:

| User Intent | Reference |
|---|---|
| No AI-Q checkout exists, install AIQ, clone AIQ, locate repo | `references/locate-or-clone.md` |
| Configure environment, check API keys, inspect `.env` | `references/env-and-secrets.md` |
| Backend-only local server for `aiq-research`, AIQ as an Agent Skill | `references/skill-backend.md` |
| Terminal assistant, CLI-only run, no web UI | `references/cli.md` |
| Quick local development run, start UI/backend without containers | `references/local-web.md` |
| Default durable local deployment, Docker Compose, containers, PostgreSQL | `references/docker-compose.md` |
| Kubernetes, Helm, cluster deployment | `references/kubernetes-helm.md` |
| Foundational RAG / FRAG integration | `references/frag.md` |
| Health checks, end-to-end smoke checks, handoff to `aiq-research` | `references/validation.md` |
| Logs, unhealthy services, port conflicts, config failures | `references/troubleshooting.md` |
| Stop services, restart, rebuild, safe cleanup | `references/shutdown.md` |

## Deployment Mode Selection

If the user asks to install, deploy, set up, or run AI-Q without naming a mode, ask:

```text
How do you want to run AI-Q?

1. Skill backend - backend-only service for aiq-research w/o browser UI.
2. CLI - interactive terminal AI-Q.
3. UI - browser AI-Q app with backend and frontend.
4. Custom config - create or choose a non-default custom AI-Q config before deployment.
```

Wait for the user's answer before starting services.

Do not ask this question when the user already specified a mode, such as Docker Compose, Helm, UI, CLI, or Agent Skill backend.

Do not ask the full mode question when `aiq-research` routed here because a deep research request needs a backend. In that case, prefer Agent Skill backend and ask only for permission to start it if needed.

Map the user's choice as follows:

| Choice | Route | Default Config |
|---|---|---|
| Skill backend | `references/docker-compose.md` backend-only, or `references/skill-backend.md` for local process | `configs/config_web_default_llamaindex.yml` |
| CLI | `references/cli.md` | `configs/config_cli_default.yml` |
| UI | `references/local-web.md` or full Docker Compose | `configs/config_web_default_llamaindex.yml` |
| Custom config | Route to the future `aiq-configure` skill, then return here after a config exists | Generated or selected config |

If the user only says "deploy AIQ", use this default path:

1. Read `references/locate-or-clone.md`.
2. Read `references/env-and-secrets.md`.
3. Read `references/docker-compose.md`.
4. Read `references/validation.md`.

If the user asks for AI-Q as an Agent Skill, use `skill-backend.md` when running locally without containers. If the user asks for a quick dev run, use `local-web.md` instead of Docker Compose. If they explicitly ask for a terminal-only assistant, use `cli.md`. If they explicitly ask for Kubernetes or Helm, use `kubernetes-helm.md`.

## Required Workflow

1. Locate or clone the AI-Q repository.
2. Confirm the expected repository files exist.
3. Create `deploy/.env` from `deploy/.env.example` only when missing.
4. If the deployment mode is ambiguous, ask the Deployment Mode Selection question.
5. Check runtime prerequisites and required environment variables for the selected deployment path. Never print secret values.
6. Start the selected deployment path.
7. Run basic validation from `references/validation.md`.
8. Tell the user the verified `AIQ_SERVER_URL` for `aiq-research`.

## Handoff Contract

`aiq-research` needs a reachable AI-Q server URL. If the backend is on the default port, no extra configuration is needed:

```bash
AIQ_SERVER_URL=http://localhost:8000
```

If the backend runs elsewhere, tell the user to set:

```bash
export AIQ_SERVER_URL="http://localhost:<PORT>"
```

Do not continue into deep research unless the user asks for it. This skill's success criterion is a deployed and validated server, not report generation quality.
