---
name: aiq-configure
description: Experimental. Use when creating, editing, or selecting custom NVIDIA AI-Q Blueprint workflow config files for Agent Skill backend, CLI, UI, FRAG, model/provider, source, sandbox, or auth-related deployment needs before AI-Q is started.
license: Apache-2.0
compatibility: Claude Code, OpenCode, Codex, and Agent Skills-compatible tools. Requires access to an AI-Q repository checkout.
metadata:
  version: "0.1.0"
  github-url: "https://github.com/NVIDIA-AI-Blueprints/aiq"
  tags: "nvidia aiq blueprint configuration experimental agent-skills"
allowed-tools: Read Write Edit Bash
---

# AIQ Configure Skill

This experimental skill helps create or select an AI-Q workflow config file before deployment.

## Boundary

- Owns AI-Q config files under `configs/`.
- Does not start, stop, or validate running services.
- Does not collect or print secrets.
- Hands the selected config path back to `aiq-deploy`.

## Workflow

1. Ask what runtime the config must support: Skill backend, CLI, UI, FRAG, or another explicit target.
2. Choose the closest base config:
   - Skill backend or UI: `configs/config_web_default_llamaindex.yml`
   - CLI: `configs/config_cli_default.yml`
   - FRAG: `configs/config_web_frag.yml`
   - AI-Q runtime DeepAgents skills or sandbox: `configs/config_skills.yml`
3. Copy to a new user-approved path such as `configs/config_custom_<name>.yml`. Do not overwrite an existing config unless the user explicitly asks.
4. Use environment-variable references for secrets. Never write raw API keys into config files.
5. For Skill backend or UI configs, ensure the config remains API-enabled with `general.front_end._type: aiq_api`.
6. Return the config path, required environment variables, and compatible `aiq-deploy` route.

## Guardrails

- Keep custom configs minimal. Change only the fields needed for the user's stated deployment.
- Do not conflate this Agent Skill with AI-Q runtime DeepAgents skills. `configs/config_skills.yml` is only for the AI-Q research agent's internal skill/sandbox behavior.
- If the user needs RAG Blueprint deployed for FRAG, hand off to the RAG Blueprint skill when available. This skill only configures AI-Q to use reachable RAG endpoints.
- If the requested config needs authentication, describe the required auth settings but leave implementation details to the user's environment.
