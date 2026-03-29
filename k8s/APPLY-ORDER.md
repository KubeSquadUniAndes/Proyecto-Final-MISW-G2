# k8scopy - Production Deployment for AWS EKS with Istio Ambient Mode

## Prerequisites

1. **AWS EKS cluster** running with Kubernetes >=1.28
2. **Istio** installed in ambient mode:
   ```bash
   istioctl install --set profile=ambient
   ```
3. **Kubernetes Gateway API CRDs** installed:
   ```bash
   kubectl get crd gateways.gateway.networking.k8s.io || \
     kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml
   ```
4. **Metrics Server** running (required for HPA):
   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   ```
5. **gp3 StorageClass** available (default on EKS). Currently postgres uses ephemeral storage (no PVC) for minikube. Uncomment volume lines in `06-postgres.yaml` for production.

## Apply Order

```bash
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-secrets.yaml
kubectl apply -f 02-waypoint.yaml
kubectl apply -f 03-gateway.yaml
kubectl apply -f 04-services.yaml
kubectl apply -f 05-destination-rules.yaml   # MUST exist before pods send traffic (avoids 503)
kubectl apply -f 06-postgres.yaml             # DB ready before app pods connect
kubectl apply -f 07-http-routes.yaml
kubectl apply -f 08-deployments.yaml          # traffic starts flowing, all deps in place
kubectl apply -f 09-hpa.yaml
kubectl apply -f 10-pdb.yaml
```

Or all at once (numbered files ensure correct ordering):
```bash
kubectl apply -f k8scopy/
```

## Architecture Decisions

### Gateway vs Waypoint (your question answered)

| Component | Purpose | External traffic? |
|---|---|---|
| `travelhub-gateway` (03) | **Ingress Gateway** — entry point for traffic FROM outside the cluster. On EKS, creates an NLB. Uses `gatewayClassName: istio`. | YES |
| `waypoint-private` (02) | **Waypoint Proxy** — handles L7 policies (AuthorizationPolicy, retries, traffic shifting) for east-west traffic INSIDE the mesh. Uses `gatewayClassName: istio-waypoint`. | NO |

**You need BOTH.** The waypoint handles service-to-service policies; the gateway handles north-south ingress. They serve different purposes and do not replace each other.

### Scalability Strategy (two layers)

**Layer 1 - Immediate (Istio DestinationRules):**
- Outlier detection ejects pods returning 3 consecutive 5xx errors for 30 seconds
- Traffic is redirected to healthy replicas instantly
- Max 50% of pods can be ejected to prevent total outage

**Layer 2 - Sustained (Kubernetes HPA):**
- Memory > 60% of requests → scale up (your requirement)
- CPU > 70% of requests → scale up (safety net)
- Scale-up is aggressive: up to 2 pods every 60s, stabilization window of 30s
- Scale-down is conservative: 1 pod every 120s, stabilization window of 5min
- Min 2 replicas, max 8 replicas per service

### Availability Guarantees

- **PodDisruptionBudgets**: at least 1 pod always available during node drains/upgrades
- **Pod anti-affinity**: replicas prefer different nodes (spread across AZs on EKS)
- **Rolling updates**: `maxUnavailable: 0` ensures zero downtime during deploys
- **Readiness probes**: unhealthy pods are removed from Service endpoints
- **PostgreSQL**: Deployment with ephemeral storage (minikube). For production, uncomment PVC lines in `06-postgres.yaml` or use Amazon RDS.

## Files Not Included (intentionally)

- **`istio-operator.yaml`**: Istio should be installed via `istioctl` or Helm, not applied as a manifest
- **`virtual-services.yaml`**: Replaced by HTTPRoutes (Gateway API), which is the modern Istio-recommended approach for ambient mode
- **Ingress (old-style)**: Replaced by the Gateway API `Gateway` resource
