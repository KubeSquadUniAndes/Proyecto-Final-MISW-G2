#!/usr/bin/env bash
# deploy-reservas-pagos.sh
# Build, push to ECR y rollout restart en EKS para reservas_ms y pagos_ms
#
# Uso:
#   ./k8s/deploy-reservas-pagos.sh              # despliega ambos
#   ./k8s/deploy-reservas-pagos.sh reservas     # solo reservas_ms
#   ./k8s/deploy-reservas-pagos.sh pagos        # solo pagos_ms

set -euo pipefail

# ── Configuración ────────────────────────────────────────────────────────────
AWS_ACCOUNT="780522923809"
AWS_REGION="us-east-1"
ECR_BASE="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/travelhub"
NAMESPACE="workloads"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-both}"   # both | reservas | pagos

# ── Colores ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()    { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── ECR login ────────────────────────────────────────────────────────────────
ecr_login() {
  info "Autenticando en ECR (${AWS_REGION})..."
  aws ecr get-login-password --region "${AWS_REGION}" \
    | docker login --username AWS --password-stdin "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
}

# ── Build + Push ─────────────────────────────────────────────────────────────
build_and_push() {
  local service="$1"      # reservas | pagos
  local dir="$2"          # reservas_ms | pagos_ms
  local ecr_repo="$3"     # reservasms | pagosms
  local image="${ECR_BASE}/${ecr_repo}:latest"

  info "=== ${service} ==="
  info "Directorio : ${REPO_ROOT}/${dir}"
  info "Imagen     : ${image}"

  info "Building imagen (--platform linux/amd64)..."
  docker build \
    --platform linux/amd64 \
    --no-cache \
    -t "${image}" \
    "${REPO_ROOT}/${dir}"

  info "Pusheando a ECR..."
  docker push "${image}"
  info "✅ Push completado: ${image}"
}

# ── Rollout restart en EKS ───────────────────────────────────────────────────
rollout_restart() {
  local deployment="$1"

  info "Ejecutando rollout restart: ${deployment} (ns: ${NAMESPACE})..."
  kubectl rollout restart deployment/"${deployment}" -n "${NAMESPACE}"
  info "Esperando rollout..."
  kubectl rollout status deployment/"${deployment}" -n "${NAMESPACE}" --timeout=120s
  info "✅ ${deployment} actualizado correctamente."
}

# ── Main ─────────────────────────────────────────────────────────────────────
ecr_login

case "${TARGET}" in
  reservas)
    build_and_push "reservas_ms" "reservas_ms" "reservasms"
    rollout_restart "reservas-deployment"
    ;;
  pagos)
    build_and_push "pagos_ms"    "pagos_ms"    "pagosms"
    rollout_restart "pagos-deployment"
    ;;
  both)
    build_and_push "reservas_ms" "reservas_ms" "reservasms"
    build_and_push "pagos_ms"    "pagos_ms"    "pagosms"
    rollout_restart "reservas-deployment"
    rollout_restart "pagos-deployment"
    ;;
  *)
    fail "Argumento inválido: '${TARGET}'. Usa: both | reservas | pagos"
    ;;
esac

echo ""
info "🚀 Deploy finalizado. Pods actuales:"
kubectl get pods -n "${NAMESPACE}" \
  -l 'app in (reservas-app,pagos-app)' \
  --sort-by='.metadata.creationTimestamp'
