#!/usr/bin/env bash
# tf-apply.sh – Import existing AWS resources into Terraform state before apply.
# Run from terraform/envs/prod/
set -euo pipefail

PROJECT="travelhub"
ENV="prod"

# ── Helpers ───────────────────────────────────────────────────────────────────
ecr_exists()   { aws ecr describe-repositories --repository-names "$1" &>/dev/null; }
iam_role_exists() { aws iam get-role --role-name "$1" &>/dev/null; }
rds_subnet_exists() { aws rds describe-db-subnet-groups --db-subnet-group-name "$1" &>/dev/null; }
in_state() { terraform state list "$1" &>/dev/null; }

# ── ECR Repositories ─────────────────────────────────────────────────────────
ECR_SERVICES=(
  "users-ms"
  "login-handler-ms"
  "reservasms"
  "notificacionesms"
  "hospedajesms"
  "detectoranomaliasms"
)

for svc in "${ECR_SERVICES[@]}"; do
  repo="$PROJECT/$svc"
  tf_addr="module.ecr.aws_ecr_repository.services[\"$svc\"]"
  tf_policy_addr="module.ecr.aws_ecr_lifecycle_policy.services[\"$svc\"]"

  if ecr_exists "$repo"; then
    if ! in_state "$tf_addr"; then
      echo "  → Importing ECR repo: $repo"
      terraform import "$tf_addr" "$repo"
    else
      echo "  ✓ ECR repo already in state: $repo"
    fi

    # Lifecycle policy (may not exist yet)
    if aws ecr get-lifecycle-policy --repository-name "$repo" &>/dev/null; then
      if ! in_state "$tf_policy_addr"; then
        echo "  → Importing ECR lifecycle policy: $repo"
        terraform import "$tf_policy_addr" "$repo"
      else
        echo "  ✓ ECR lifecycle policy already in state: $repo"
      fi
    fi
  else
    echo "  + ECR repo not found, will create: $repo"
  fi
done

# ── IAM Role – EKS Control Plane ─────────────────────────────────────────────
EKS_CLUSTER_ROLE="${PROJECT}-${ENV}-eks-cluster-role"
tf_eks_role="module.eks.aws_iam_role.eks_cluster"
if iam_role_exists "$EKS_CLUSTER_ROLE"; then
  if ! in_state "$tf_eks_role"; then
    echo "  → Importing IAM role: $EKS_CLUSTER_ROLE"
    terraform import "$tf_eks_role" "$EKS_CLUSTER_ROLE"
  else
    echo "  ✓ IAM role already in state: $EKS_CLUSTER_ROLE"
  fi
else
  echo "  + IAM role not found, will create: $EKS_CLUSTER_ROLE"
fi

# ── IAM Role – EKS Node Group ────────────────────────────────────────────────
EKS_NODE_ROLE="${PROJECT}-${ENV}-eks-node-role"
tf_eks_node_role="module.eks.aws_iam_role.eks_nodes"
if iam_role_exists "$EKS_NODE_ROLE"; then
  if ! in_state "$tf_eks_node_role"; then
    echo "  → Importing IAM role: $EKS_NODE_ROLE"
    terraform import "$tf_eks_node_role" "$EKS_NODE_ROLE"
  else
    echo "  ✓ IAM role already in state: $EKS_NODE_ROLE"
  fi
else
  echo "  + IAM role not found, will create: $EKS_NODE_ROLE"
fi

# ── RDS (DB Instance + Subnet Group) ─────────────────────────────────────────
RDS_SUBNET_GROUP="${PROJECT}-${ENV}-db-subnet-group"
RDS_INSTANCE="${PROJECT}-${ENV}-postgres"
tf_rds_subnet="module.rds.aws_db_subnet_group.main"
tf_rds_instance="module.rds.aws_db_instance.main"

# Retrieve the VPC ID Terraform has in state (created by module.vpc)
TARGET_VPC=$(terraform show -json 2>/dev/null \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for mod in data.get('values', {}).get('root_module', {}).get('child_modules', []):
  if mod.get('address') == 'module.vpc':
    for r in mod.get('resources', []):
      if r.get('type') == 'aws_vpc':
        print(r['values']['id'])
        sys.exit(0)
" 2>/dev/null || true)

# Detect existing DB instance
INSTANCE_VPC=""
if aws rds describe-db-instances --db-instance-identifier "$RDS_INSTANCE" &>/dev/null; then
  INSTANCE_VPC=$(aws rds describe-db-instances \
    --db-instance-identifier "$RDS_INSTANCE" \
    --query "DBInstances[0].DBSubnetGroup.VpcId" --output text 2>/dev/null || true)

  if [[ -n "$TARGET_VPC" && -n "$INSTANCE_VPC" && "$INSTANCE_VPC" != "$TARGET_VPC" ]]; then
    echo ""
    echo "  ✗ FATAL: RDS instance '$RDS_INSTANCE' exists in VPC $INSTANCE_VPC"
    echo "    but Terraform's target VPC is $TARGET_VPC."
    echo ""
    echo "    AWS does not allow moving an RDS instance between VPCs."
    echo "    The instance has deletion_protection=true, so it cannot be auto-deleted."
    echo ""
    echo "    Manual steps required:"
    echo "    1. Snapshot the instance (if data must be preserved):"
    echo "       aws rds create-db-snapshot \\"
    echo "         --db-instance-identifier $RDS_INSTANCE \\"
    echo "         --db-snapshot-identifier ${RDS_INSTANCE}-manual-backup"
    echo "    2. Disable deletion protection:"
    echo "       aws rds modify-db-instance \\"
    echo "         --db-instance-identifier $RDS_INSTANCE \\"
    echo "         --no-deletion-protection --apply-immediately"
    echo "    3. Delete the instance (wait for completion):"
    echo "       aws rds delete-db-instance \\"
    echo "         --db-instance-identifier $RDS_INSTANCE \\"
    echo "         --skip-final-snapshot"
    echo "       aws rds wait db-instance-deleted \\"
    echo "         --db-instance-identifier $RDS_INSTANCE"
    echo "    4. Delete the orphaned subnet group:"
    echo "       aws rds delete-db-subnet-group \\"
    echo "         --db-subnet-group-name $RDS_SUBNET_GROUP"
    echo "    5. Remove stale state (if either was imported):"
    echo "       terraform state rm $tf_rds_instance 2>/dev/null || true"
    echo "       terraform state rm $tf_rds_subnet  2>/dev/null || true"
    echo "    6. Re-run this script."
    echo ""
    exit 1
  fi

  # Same VPC – import the instance if not already in state
  if ! in_state "$tf_rds_instance"; then
    echo "  → Importing RDS instance: $RDS_INSTANCE"
    terraform import "$tf_rds_instance" "$RDS_INSTANCE"
  else
    echo "  ✓ RDS instance already in state: $RDS_INSTANCE"
  fi
else
  echo "  + RDS instance not found, will create: $RDS_INSTANCE"
fi

# Handle subnet group (only after instance VPC check passes)
if rds_subnet_exists "$RDS_SUBNET_GROUP"; then
  EXISTING_VPC=$(aws rds describe-db-subnet-groups \
    --db-subnet-group-name "$RDS_SUBNET_GROUP" \
    --query "DBSubnetGroups[0].VpcId" --output text 2>/dev/null || true)

  if [[ -n "$TARGET_VPC" && -n "$EXISTING_VPC" && "$EXISTING_VPC" != "$TARGET_VPC" ]]; then
    # No DB instance blocking (we would have exited above), safe to delete
    echo "  ⚠ Subnet group '$RDS_SUBNET_GROUP' is in old VPC $EXISTING_VPC. Deleting so Terraform recreates it..."
    aws rds delete-db-subnet-group --db-subnet-group-name "$RDS_SUBNET_GROUP"
    if in_state "$tf_rds_subnet"; then
      terraform state rm "$tf_rds_subnet"
    fi
    echo "  ✓ Deleted. Terraform will create a new subnet group in VPC $TARGET_VPC."
  elif ! in_state "$tf_rds_subnet"; then
    echo "  → Importing RDS subnet group: $RDS_SUBNET_GROUP"
    terraform import "$tf_rds_subnet" "$RDS_SUBNET_GROUP"
  else
    echo "  ✓ RDS subnet group already in state: $RDS_SUBNET_GROUP"
  fi
else
  echo "  + RDS subnet group not found, will create: $RDS_SUBNET_GROUP"
fi

# ── Apply ─────────────────────────────────────────────────────────────────────
echo ""
echo "Running terraform apply..."
terraform apply "$@"
