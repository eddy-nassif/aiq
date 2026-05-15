---
name: aiq-evaluation
description: Stub skill for evaluating whether a deployed NVIDIA AI-Q Blueprint research system is functioning as expected. Use for research-system validation, source/tool failure checks, install/runtime failure checks, LLM/search-provider failure checks, and report-completion reliability. Do not use for subjective report-quality scoring.
license: Apache-2.0
compatibility: Claude Code, OpenCode, Codex, and Agent Skills-compatible tools. Requires a deployed AI-Q server and stable validation inputs.
metadata:
  version: "0.1.0"
  github-url: "https://github.com/NVIDIA-AI-Blueprints/aiq"
  tags: "nvidia aiq blueprint evaluation validation agent-skills"
allowed-tools: Read Bash
---

# AIQ Evaluation Skill

This is a placeholder skill location for future AI-Q research-system evaluation workflows.

## Intended Scope

Use this skill to validate whether the deployed AI-Q system can reliably complete research workflows without infrastructure or integration failures.

Examples:

- required services are installed and reachable
- configured source providers are reachable
- configured model and search providers respond
- representative research requests complete successfully
- reports include expected structural elements such as citations and source references
- failures identify whether the likely cause is install, runtime, source access, model/search provider, or AI-Q orchestration

## Non-Goals

- Do not score the subjective quality of the report argument.
- Do not rank reports as good or bad based on writing style.
- Do not replace basic deploy validation in `aiq-deploy`.
- Do not run expensive deep research checks by default.

## Relationship To Other AI-Q Skills

- Use `aiq-deploy` first when AI-Q is not running.
- Use `aiq-research` for normal routed chat, async jobs, polling, and report retrieval.
- Use `aiq-evaluation` only when the user wants to validate the research system itself.

## Current Status

This skill is intentionally a stub. Future work should add deterministic validation profiles, expected fixtures, source/tool checks, and explicit cost controls before enabling automated research-system evaluation.
