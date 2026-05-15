# Environment And Secrets

Use `deploy/.env` as the local deployment source of truth.

## Create Missing Env File

Do not overwrite an existing file.

```bash
if [ ! -f deploy/.env ]; then
  cp deploy/.env.example deploy/.env
  echo "created deploy/.env from deploy/.env.example"
fi
```

## Presence-Only Secret Check

Never print secret values.

```bash
python3 - <<'PY'
from pathlib import Path

env = Path("deploy/.env")
values = {}
for line in env.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    values[key.strip()] = value.strip()

def present(key: str) -> str:
    return "SET" if values.get(key) else "MISSING"

for key in [
    "NVIDIA_API_KEY",
    "TAVILY_API_KEY",
    "SERPER_API_KEY",
    "EXA_API_KEY",
    "NAT_JOB_STORE_DB_URL",
    "AIQ_CHECKPOINT_DB",
    "RAG_SERVER_URL",
    "RAG_INGEST_URL",
]:
    print(f"{key}={present(key)}")

print(f"BACKEND_CONFIG={values.get('BACKEND_CONFIG') or 'default'}")
PY
```

Core hosted-model usage requires `NVIDIA_API_KEY`. Web research requires at least one configured search provider key for the selected config.

If required values are missing, stop and ask the user to fill `deploy/.env`. Do not ask them to paste secrets into chat.
