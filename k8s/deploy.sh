#!/usr/bin/env bash
# deploy.sh - applies all top-level k8s manifests in dependency order.
# Usage: ./k8s/deploy.sh [apply|delete]

set -euo pipefail

ACTION="${1:-apply}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FILES=(
  "00-namespace.yaml"
  "00b-service-accounts.yaml"
  "01b-secrets-configmaps.yaml"
  "02-waypoint.yaml"
  "03-gateway.yaml"
  "04-services.yaml"
  "05-destination-rules.yaml"
  "07-http-routes.yaml"
  "08-deployments.yaml"
  "09-hpa.yaml"
  "10-pdb.yaml"
  "11-authorization-policies.yaml"
)

if [[ "${ACTION}" != "apply" && "${ACTION}" != "delete" ]]; then
  echo "Usage: $0 [apply|delete]"
  exit 1
fi

echo "Action: kubectl ${ACTION}"

if [[ "${ACTION}" == "apply" ]]; then
  for file in "${FILES[@]}"; do
    echo "Applying ${file}"
    kubectl apply -f "${SCRIPT_DIR}/${file}"
  done
  echo "All manifests applied."
else
  for ((idx=${#FILES[@]}-1; idx>=0; idx--)); do
    file="${FILES[$idx]}"
    echo "Deleting ${file}"
    kubectl delete -f "${SCRIPT_DIR}/${file}" --ignore-not-found
  done
  echo "All manifests deleted."
fi