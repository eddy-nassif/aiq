# End-To-End Validation

Use this reference when the user wants to verify that a deployed AI-Q research system works end to end. This is integration validation, not subjective report-quality scoring and not a skill-behavior test.

## Profiles

| Profile | Use When | Checks |
|---|---|---|
| `smoke` | After basic deploy validation or before a longer run | health, async agents, shallow `/chat`, no obvious auth/model errors |
| `deep-research` | User asks whether deep research works | async submit, poll, state, report fetch, citation/source structure |
| `source-coverage` | User asks whether configured sources work | source inventory, effective tool availability, source-specific probes, observed tool calls, returned evidence |
| `file-upload` | File upload or document-grounded research must work | upload/ingest a small fixture, ask for a unique sentinel fact, verify the report uses it |
| `frag` | Foundational RAG endpoints are configured | `RAG_SERVER_URL`, `RAG_INGEST_URL`, ingest reachability, retrieval-backed answer |
| `full` | Release signoff or serious incident debugging | all applicable profiles, with timeout and cost confirmation |

Ask before running `deep-research`, `source-coverage`, `file-upload`, `frag`, or `full`. A deep research validation report commonly takes 7-20 minutes; observed report runs can land at the 20-minute mark with high token and tool-call usage. Use a timeout above the normal upper bound, such as 30 minutes.

A completed report may cite only a subset of sources it read. For example, an observed run cited 10 sources in the final report after reading 56 distinct URLs. This is not a failure by itself; report cited-source count and distinct URLs read separately when available.

## Prompt Strategy

Use fixed prompts with deterministic assertions. Do not compare generated prose against a golden report as the primary signal; report wording is nondeterministic and will create noisy failures.

An example report can be useful as a schema reference for expected sections, citations, and artifact fields. Do not require exact phrasing, paragraph order, or analytical conclusions to match the example.

Use a small baseline prompt set:

| Check | Prompt | Expected Signal |
|---|---|---|
| Shallow model | `Briefly confirm AI-Q is responding with one sentence.` | `/chat` returns a non-empty model response without auth or provider errors |
| Source-backed research | `Create a short sourced report explaining what NVIDIA AI-Q Blueprint is used for. Include three bullets and cite the sources you used.` | async job completes, report is non-empty, sources/citations are present |
| File fixture | `According to the uploaded validation document, what is the sentinel phrase and what does it prove about retrieval?` | report includes the exact sentinel phrase from the uploaded file |
| RAG fixture | `Using the configured RAG source, answer the question that mentions AIQ_VALIDATION_SENTINEL and cite the retrieved source.` | answer includes the sentinel fact and retrieval/source evidence |

For the file or RAG checks, create a tiny fixture with a unique value such as:

```text
AIQ_VALIDATION_SENTINEL_20260518: This sentence exists only to prove that AI-Q can retrieve uploaded validation content.
```

The sentinel should be unique to the run. Passing means the system retrieved and used the fixture, not that the model wrote a good report.

## Source Coverage

Use `source-coverage` when the user asks whether all configured sources can be used. Do not require every configured source to appear in every normal deep research report; source use depends on the query and agent planning. For example, a cheese-making report may correctly skip internal enterprise search even when enterprise sources are enabled.

1. Inventory configured sources with `GET /v1/data_sources` when available, or from the selected config's `data_source_registry`.
2. Map each source ID to its configured tools or function groups, accounting for explicit agent `tools` and `exclude_tools`.
3. Run source-specific probes only for sources the user wants validated.
4. Inspect job state, event-store/tool-call data, and final citations or source artifacts.
5. Report a matrix with `configured`, `available`, `attempted`, `returned_evidence`, and `cited`.

Treat URLs, citation keys, document IDs, chunks, or retrieved file references as valid evidence depending on the source type. Enterprise MCP or ECI-style sources may not produce public URLs; do not fail them for lacking URL citations if they return source-specific evidence.

Only fail `source-coverage` when a selected source is expected to be usable but is unavailable, never attempted by its source-specific probe, returns no evidence, or returns an auth/config error. For regular `deep-research`, an unused configured source is a caution or observation to review, not an automatic failure.

## Direct LLM Endpoint Preflight

Direct provider checks can catch invalid keys, blocked egress, or unavailable provider APIs before running AI-Q requests. They are optional because they do not prove AI-Q is wired to the provider correctly. The shallow `/chat` check remains the AI-Q-level model-backed validation.

Run direct checks only when the selected config exposes the provider and the needed key is present. These examples assume deployment environment variables are already loaded into the command environment. Do not print API keys, request headers, or full provider responses.

For the default NVIDIA-hosted NIM path, check the OpenAI-compatible model catalog endpoint:

```bash
test -n "$NVIDIA_API_KEY" && \
  curl -fsS \
    -H "Authorization: Bearer $NVIDIA_API_KEY" \
    "https://integrate.api.nvidia.com/v1/models" \
    >/dev/null && \
  echo "nvidia_llm_endpoint=reachable"
```

For configs that explicitly use OpenAI, check the OpenAI model catalog endpoint:

```bash
test -n "$OPENAI_API_KEY" && \
  curl -fsS \
    -H "Authorization: Bearer $OPENAI_API_KEY" \
    "https://api.openai.com/v1/models" \
    >/dev/null && \
  echo "openai_llm_endpoint=reachable"
```

For custom OpenAI-compatible provider URLs, use the base URL from the selected config and append `/models` only when that provider supports the catalog endpoint.

If a direct provider check passes but `/chat` fails, treat the provider as reachable and continue troubleshooting AI-Q config, model name, auth, or routing. If the direct provider check fails, report only the provider and failure type; do not print secret values.

## Suggested Sequence

1. Resolve `AIQ_SERVER_URL`; default to `http://localhost:8000` only when unset.
2. Run basic deploy validation if it has not already passed.
3. Confirm required secrets are present without printing values.
4. Run optional direct LLM endpoint preflight when useful.
5. Run `smoke`.
6. Run `deep-research` when the user wants research-system validation.
7. Run `source-coverage` only when the user wants each configured or selected source validated.
8. Run `file-upload` only when the selected deployment exposes file upload or document ingestion.
9. Run `frag` only when `RAG_SERVER_URL` or `RAG_INGEST_URL` is configured.
10. Summarize pass/fail by subsystem and hand the verified server URL back to `aiq-research`.
11. Include runtime, job ID, token count, tool-call count, cited-source count, and distinct URLs read when those values are available.

## API Checks

Use the `aiq-research` helper for API operations when available:

```bash
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py health
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py agents
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py chat "Briefly confirm AI-Q is responding with one sentence."
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py research "Create a short sourced report explaining what NVIDIA AI-Q Blueprint is used for. Include three bullets and cite the sources you used."
```

If the helper returns a `job_id`, keep the job ID in the validation summary and inspect status/state/report:

```bash
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py status "$JOB_ID"
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py state "$JOB_ID"
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py report "$JOB_ID"
```

Use SSE streaming as an optional signal when debugging event delivery:

```bash
AIQ_SERVER_URL="$AIQ_SERVER_URL" python3 .agents/skills/aiq-research/scripts/aiq.py stream "$JOB_ID"
```

## Pass Criteria

Mark a validation profile as passed only when the relevant observable signals are present:

- backend health endpoint returns success
- async agents endpoint returns a usable agent list
- shallow `/chat` returns non-empty model output
- deep research job reaches `completed` or `success`
- final report endpoint returns non-empty report content
- job state or event store contains useful progress/artifact data
- source-backed prompt includes citations, source URLs, or source references
- cited-source count may be lower than the number of distinct URLs read; this is normal if the final report cites a representative subset
- file/RAG fixture prompt includes the sentinel fact from the fixture source
- no auth, model provider, search provider, retrieval, database, or report-generation errors appear in status, state, logs, or returned content

## Failure Classification

| Symptom | Likely Area | Next Action |
|---|---|---|
| `/health` fails | deployment/runtime | return to basic validation and troubleshooting |
| health passes, `/chat` fails | model endpoint, auth, or route config | check required env keys and selected config |
| agents endpoint fails | async API compatibility or backend route config | verify the deployed config exposes async jobs |
| submit succeeds, polling never completes | orchestration, worker, or provider timeout | inspect job status, state, and backend logs |
| report endpoint is empty after success | report generation or persistence | inspect state artifacts and job storage |
| source-backed prompt has no citations | source/search provider or report formatting | check provider env keys and source-tool logs |
| fixture upload succeeds but sentinel is missing | retrieval or file reachability to the agent | verify upload/ingest endpoint, file store, and retrieval config |
| RAG variables are set but retrieval fails | RAG service or ingest/retrieval URL | verify `RAG_SERVER_URL`, `RAG_INGEST_URL`, and RAG service health |
| errors mention invalid key, unauthorized, or forbidden | secret/auth configuration | ask user to update keys without printing current values |
