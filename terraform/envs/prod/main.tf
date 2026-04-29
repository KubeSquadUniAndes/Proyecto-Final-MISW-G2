terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket  = "travelhub-tfstate-universidad"
    key     = "terraform/state.tfstate"
    region  = "us-east-1"
    encrypt = true
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Secrets Manager — app secrets ─────────────────────────────────────────────
# These secrets must be created manually before running terraform:
#   aws secretsmanager create-secret --name travelhub/rds/password --secret-string "..."
#   aws secretsmanager create-secret --name travelhub/app/jwt-secret --secret-string "..."
#   aws secretsmanager create-secret --name travelhub/reservas/aes-key --secret-string "..."

# ── Secrets Manager ──────────────────────────────────────────────────────────
# Sensitive values are passed via environment variables in the CI/CD pipeline:
#   TF_VAR_db_password, TF_VAR_jwt_secret, TF_VAR_aes_encryption_key, TF_VAR_internal_api_key
module "secrets" {
  source = "../../modules/secrets"

  project            = var.project
  environment        = var.environment
  db_password        = var.db_password
  jwt_secret         = var.jwt_secret
  aes_encryption_key = var.aes_encryption_key
  internal_api_key   = var.internal_api_key
}

# ── VPC ───────────────────────────────────────────────────────────────────────
module "vpc" {
  source = "../../modules/vpc"

  project     = var.project
  environment = var.environment
  aws_region  = var.aws_region
}

# ── ECR Repositories ──────────────────────────────────────────────────────────
module "ecr" {
  source = "../../modules/ecr"

  project     = var.project
  environment = var.environment
  services    = ["users-ms", "login-handler-ms", "reservasms", "notificacionesms", "hospedajesms", "detectoranomaliasms"]
}

# ── EKS Cluster ───────────────────────────────────────────────────────────────
module "eks" {
  source = "../../modules/eks"

  project         = var.project
  environment     = var.environment
  aws_region      = var.aws_region
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  cluster_version = var.cluster_version
}

# ── RDS PostgreSQL ────────────────────────────────────────────────────────────
module "rds" {
  source = "../../modules/rds"

  project                    = var.project
  environment                = var.environment
  vpc_id                     = module.vpc.vpc_id
  private_subnets            = module.vpc.private_subnet_ids
  eks_security_group         = module.eks.node_security_group_id
  eks_cluster_security_group = module.eks.cluster_security_group_id
  db_password                = var.db_password
}
