# Troubleshooting

Use this when deployment starts but AI-Q is unhealthy or unreachable.

## First Checks

```bash
pwd
git status -sb
test -f deploy/.env
grep -E '^(PORT|FRONTEND_PORT|BACKEND_CONFIG)=' deploy/.env || true
```

Do not print secret values.

## Service Logs

Docker Compose:

```bash
docker logs aiq-agent --tail 100
docker logs aiq-blueprint-ui --tail 100
docker logs aiq-postgres --tail 100
```

Kubernetes:

```bash
kubectl get pods
kubectl logs deploy/<deployment-name> --tail=100
```

## Common Failure Areas

- Port conflict on backend, frontend, or PostgreSQL.
- Missing `NVIDIA_API_KEY` or search provider key.
- Selected config file does not exist.
- `NAT_JOB_STORE_DB_URL` or `AIQ_CHECKPOINT_DB` does not match the running PostgreSQL service.
- Docker container was recreated and lost an external RAG network connection.
- Backend is healthy but UI points at the wrong backend URL.

After fixing a failure, rerun `validation.md`.
