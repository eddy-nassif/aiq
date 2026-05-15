<!--
SPDX-FileCopyrightText: Copyright (c) 2025-2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
SPDX-License-Identifier: Apache-2.0
-->

# Agent Skills for Coding Harnesses

AI-Q includes portable Agent Skills for coding harnesses that support skill-style instructions and helper scripts.

- `aiq-deploy` helps an assistant clone or locate AI-Q, deploy it locally or in self-hosted environments, verify basic system health, troubleshoot, rebuild, and stop services.
- `aiq-configure` is an experimental helper for creating, editing, or selecting custom AI-Q workflow config files before deployment.
- `aiq-research` lets an assistant call a running local or self-hosted AI-Q Blueprint server for routed `/chat` requests and async deep research job lifecycle operations.
- `aiq-evaluation` is a placeholder surface for future research-system validation workflows. It is for checking whether source access, install/runtime, model/search provider, or orchestration failures are causing research workflows to fail. It is not for subjective report-quality scoring.

The packaged skills live at:

```text
.agents/skills/aiq-deploy/
.agents/skills/aiq-configure/
.agents/skills/aiq-research/
.agents/skills/aiq-evaluation/
```

Each installed skill directory must contain `SKILL.md` at its root. The deploy skill keeps path-specific guidance under `.agents/skills/aiq-deploy/references/` so agents only load the deployment mode they need.

## Recommended Flow

Use the skills together rather than blending their responsibilities:

1. Use `aiq-deploy` to get AI-Q running.
2. Use `aiq-configure` only when the user wants an experimental custom config instead of a default config.
3. Use `aiq-deploy` validation checks to confirm the backend and async-agent API are reachable. Confirm the UI only when that deployment mode intentionally starts it.
4. Hand the verified `AIQ_SERVER_URL` to `aiq-research`.
5. Use `aiq-research` for routed chat, async research, polling, report retrieval, streaming, and cancellation.
6. Use `aiq-evaluation` only for future research-system validation workflows once those profiles are defined.

For local non-container use, the deploy skill should prefer the backend-only Agent Skill entry point:

```bash
./scripts/start_as_skill.sh --config_file configs/config_web_default_llamaindex.yml --port 8000
```

This starts the AI-Q API backend required by `aiq-research` without starting the browser UI.

## Example Invocations

After the skills are installed, users can ask their coding harness for AI-Q actions in natural language. These prompts should route to `aiq-deploy` unless they are explicitly asking to run research against an already healthy backend:

| User Prompt | Expected Route |
|---|---|
| "deploy AI-Q" | `aiq-deploy` chooses the default deployment path, validates the backend, and returns `AIQ_SERVER_URL`. |
| "clone AIQ and run it" | `aiq-deploy` locates or clones `NVIDIA-AI-Blueprints/aiq`, checks required environment values, then starts the selected default deployment. |
| "start the AI-Q UI" | `aiq-deploy` starts a deployment mode that includes the browser UI, such as local E2E or full Docker Compose. |
| "run AI-Q with Docker Compose" | `aiq-deploy` follows the Docker Compose path. For Agent Skill backend use, it should start `aiq-agent` and dependencies without the frontend unless the user asks for UI. |
| "deploy AI-Q with Helm" | `aiq-deploy` follows the Kubernetes/Helm path and requires the user to provide or confirm cluster, namespace, registry, secret, ingress, and storage choices. |
| "create a custom AI-Q config" | `aiq-configure` experimentally creates, edits, or selects a config file, then hands the config path back to `aiq-deploy`. |
| "check why AI-Q is unhealthy" | `aiq-deploy` runs health checks, inspects logs/status, and uses the troubleshooting reference for the active deployment mode. |
| "stop AI-Q" | `aiq-deploy` follows the shutdown path and asks before destructive cleanup such as deleting Docker volumes. |

## Prerequisites

- Python 3.10 or newer.
- For `aiq-deploy`: access to this repository or permission to clone `https://github.com/NVIDIA-AI-Blueprints/aiq`, plus the selected runtime such as Docker Compose, Node/npm for local web mode, or kubectl/Helm for Kubernetes mode.
- For `aiq-configure`: access to an AI-Q repository checkout. The skill is experimental and should change only the fields needed for the user's deployment target.
- For `aiq-research`: a local or self-hosted AI-Q Blueprint server, usually at `http://localhost:8000`. Set `AIQ_SERVER_URL` only when using a different local or self-hosted server URL.
- For `aiq-evaluation`: a deployed AI-Q server and stable validation inputs. The skill is currently a stub.

## Claude Code

Claude Code supports repo-local skills under `.claude/skills/`. This repository keeps those paths as compatibility symlinks:

```text
.claude/skills/aiq-deploy -> ../../.agents/skills/aiq-deploy
.claude/skills/aiq-configure -> ../../.agents/skills/aiq-configure
.claude/skills/aiq-research -> ../../.agents/skills/aiq-research
.claude/skills/aiq-evaluation -> ../../.agents/skills/aiq-evaluation
```

To recreate the repo-local install manually:

```bash
mkdir -p .claude/skills
ln -s ../../.agents/skills/aiq-deploy .claude/skills/aiq-deploy
ln -s ../../.agents/skills/aiq-configure .claude/skills/aiq-configure
ln -s ../../.agents/skills/aiq-research .claude/skills/aiq-research
ln -s ../../.agents/skills/aiq-evaluation .claude/skills/aiq-evaluation
```

For a user-level install:

```bash
mkdir -p ~/.claude/skills
cp -R .agents/skills/aiq-deploy ~/.claude/skills/aiq-deploy
cp -R .agents/skills/aiq-configure ~/.claude/skills/aiq-configure
cp -R .agents/skills/aiq-research ~/.claude/skills/aiq-research
cp -R .agents/skills/aiq-evaluation ~/.claude/skills/aiq-evaluation
```

## Codex

For Codex or another Agent Skills-compatible tool, install the skill into the runtime's configured skills directory.

Generic install shape:

```text
<codex-skills-dir>/aiq-deploy/SKILL.md
<codex-skills-dir>/aiq-deploy/references/
<codex-skills-dir>/aiq-configure/SKILL.md
<codex-skills-dir>/aiq-research/SKILL.md
<codex-skills-dir>/aiq-research/scripts/aiq.py
<codex-skills-dir>/aiq-evaluation/SKILL.md
```

Example:

```bash
mkdir -p <codex-skills-dir>
cp -R .agents/skills/aiq-deploy <codex-skills-dir>/aiq-deploy
cp -R .agents/skills/aiq-configure <codex-skills-dir>/aiq-configure
cp -R .agents/skills/aiq-research <codex-skills-dir>/aiq-research
cp -R .agents/skills/aiq-evaluation <codex-skills-dir>/aiq-evaluation
```

Replace `<codex-skills-dir>` with the skills directory configured for your Codex environment.

## OpenCode

OpenCode loads user skills from `~/.config/opencode/skills/`.

Install with:

```bash
mkdir -p ~/.config/opencode/skills
cp -R .agents/skills/aiq-deploy ~/.config/opencode/skills/aiq-deploy
cp -R .agents/skills/aiq-configure ~/.config/opencode/skills/aiq-configure
cp -R .agents/skills/aiq-research ~/.config/opencode/skills/aiq-research
cp -R .agents/skills/aiq-evaluation ~/.config/opencode/skills/aiq-evaluation
```

Restart OpenCode or start a new session after installation.

## Verify Installation

From the parent directory containing the installed skills, run:

```bash
test -f aiq-deploy/SKILL.md
test -d aiq-deploy/references
test -f aiq-configure/SKILL.md
python3 aiq-research/scripts/aiq.py
test -f aiq-evaluation/SKILL.md
```

Expected `aiq-research/scripts/aiq.py` output starts with:

```text
Usage: aiq.py <command> [args]
```
