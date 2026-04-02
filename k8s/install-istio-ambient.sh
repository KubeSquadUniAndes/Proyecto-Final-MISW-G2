#!/usr/bin/env bash

# install-istio-ambient.sh
# Runs the Istio install steps exactly as documented in README Section 3.2.
# Usage:
#   ./k8s/install-istio-ambient.sh

set -euo pipefail

if ! command -v kubectl >/dev/null 2>&1; then
  echo "Error: kubectl is not installed." >&2
  exit 1
fi

if ! command -v istioctl >/dev/null 2>&1; then
  echo "Error: istioctl is not installed or not in PATH." >&2
  exit 1
fi

echo "==> Step 1/3: Install Gateway API CRDs"
kubectl get crd gateways.gateway.networking.k8s.io &> /dev/null || \
  kubectl apply --server-side -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.4.0/experimental-install.yaml

echo "==> Step 2/4: Run Istio precheck"
istioctl x precheck

echo "==> Step 3/4: Install Istio with ambient profile"
istioctl install --set profile=ambient --skip-confirmation

echo "==> Waiting for istiod and ztunnel to become Ready"
kubectl -n istio-system rollout status deployment/istiod --timeout=10m
kubectl -n istio-system rollout status daemonset/ztunnel --timeout=10m

echo "==> Step 4/4: Apply standard Gateway API"
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml

echo "==> Done. Executed README Section 3.2 steps exactly."
