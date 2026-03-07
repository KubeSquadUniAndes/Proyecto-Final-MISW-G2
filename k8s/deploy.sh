#!/bin/bash
# deploy.sh — applies all k8s manifests in dependency order
# Usage: ./deploy.sh [apply|delete]

set -e

ACTION=${1:-apply}
DOMAIN="api.experiment.local"   # Change to your actual domain

echo "🚀 Action: kubectl $ACTION"
echo ""

# 1. Namespaces first
echo "── Namespaces ──────────────────────────────"
kubectl $ACTION -f login-handler-ms/login-handler-ms.yaml
kubectl $ACTION -f reservas-ms/reservas-ms.yaml
kubectl $ACTION -f detector-anomalias-ms/detector-anomalias-ms.yaml
kubectl $ACTION -f notificaciones-ms/notificaciones-ms.yaml

if [ "$ACTION" = "apply" ]; then
  echo ""
  echo "✅ All manifests applied."
  echo ""
  echo "── Wait for rollouts ───────────────────────"
  kubectl rollout status deployment/login-handler-ms  -n login-handler-ms
  kubectl rollout status deployment/reservas-ms       -n reservas-ms
  kubectl rollout status deployment/detector-anomalias-ms -n detector-anomalias-ms
  kubectl rollout status deployment/notificaciones-ms -n notificaciones-ms

  echo ""
  echo "── Ingress routes ──────────────────────────"
  echo "  http://$DOMAIN/auth/docs          → login_handler_ms"
  echo "  http://$DOMAIN/reservas/docs      → reservas_ms"
  echo "  http://$DOMAIN/detector/docs      → detector_anomalias_ms"
  echo "  http://$DOMAIN/notifications/docs → notificaciones_ms"
fi