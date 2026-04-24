#!/usr/bin/env bash

# install-external-secrets.sh
# Installs External Secrets Operator and configures it to sync secrets
# from AWS Secrets Manager into Kubernetes Secrets.
#
# Prerequisites:
#   - kubectl configured to the target cluster
#   - helm installed
#   - Terraform applied (secrets already exist in Secrets Manager)
#   - EXTERNAL_SECRETS_ROLE_ARN set (from: terraform output external_secrets_role_arn)
#
# Usage:
#   export EXTERNAL_SECRETS_ROLE_ARN=$(cd terraform/envs/prod && terraform output -raw external_secrets_role_arn)
#   ./k8s/install-external-secrets.sh

set -euo pipefail

if ! command -v helm >/dev/null 2>&1; then
  echo "Error: helm is not installed." >&2
  exit 1
fi

if [[ -z "${EXTERNAL_SECRETS_ROLE_ARN:-}" ]]; then
  echo "Error: EXTERNAL_SECRETS_ROLE_ARN is not set." >&2
  echo "Run: export EXTERNAL_SECRETS_ROLE_ARN=\$(cd terraform/envs/prod && terraform output -raw external_secrets_role_arn)" >&2
  exit 1
fi

echo "==> Step 1/4: Add External Secrets Operator Helm repo"
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

echo "==> Step 2/4: Install External Secrets Operator"
helm upgrade --install external-secrets external-secrets/external-secrets \
  --namespace external-secrets \
  --create-namespace \
  --set installCRDs=true \
  --wait --timeout=5m

echo "==> Step 3/4: Patch ServiceAccount with IRSA annotation"
kubectl annotate serviceaccount external-secrets-sa \
  -n workloads \
  eks.amazonaws.com/role-arn="${EXTERNAL_SECRETS_ROLE_ARN}" \
  --overwrite

echo "==> Step 4/4: Apply ExternalSecrets manifests"
kubectl apply -f k8s/14-external-secrets.yaml

echo "==> Waiting for secrets to sync..."
sleep 15
kubectl get externalsecret -n workloads

echo "==> Done. Secrets are now managed by External Secrets Operator."
echo "    K8s Secrets are auto-synced from AWS Secrets Manager every 1h."
