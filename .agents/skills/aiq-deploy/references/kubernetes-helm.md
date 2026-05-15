# Kubernetes And Helm Deployment

Use this path only when the user explicitly asks for Kubernetes, Helm, or cluster deployment.

## Initial Checks

```bash
kubectl version --client
helm version
find deploy/helm -maxdepth 4 -name Chart.yaml -print
```

Inspect the available chart and values files before acting. Do not guess namespace, image registry, secret names, ingress, or storage values.

## Deployment Rules

- Ask only for missing cluster-specific choices.
- Do not create or delete cluster resources without confirming the target namespace and context.
- Use the repository Helm docs and values files as the source of truth.
- After deployment, run `validation.md` checks against the exposed backend URL.
