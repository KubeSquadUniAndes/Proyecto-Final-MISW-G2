terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
  }

  # Uncomment after creating the S3 bucket and DynamoDB table for state
  # backend "s3" {
  #   bucket         = "travelhub-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "travelhub-terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}

# ── VPC ───────────────────────────────────────────────────────────────────────
module "vpc" {
  source = "../modules/vpc"

  project     = var.project
  environment = var.environment
  aws_region  = var.aws_region
}

# ── ECR Repositories ──────────────────────────────────────────────────────────
module "ecr" {
  source = "../modules/ecr"

  project     = var.project
  environment = var.environment
  services    = ["users-ms", "login-handler-ms"]
}

# ── EKS Cluster ───────────────────────────────────────────────────────────────
module "eks" {
  source = "../modules/eks"

  project          = var.project
  environment      = var.environment
  aws_region       = var.aws_region
  vpc_id           = module.vpc.vpc_id
  private_subnets  = module.vpc.private_subnet_ids
  cluster_version  = var.cluster_version
}

# ── RDS PostgreSQL ────────────────────────────────────────────────────────────
module "rds" {
  source = "../modules/rds"

  project            = var.project
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnets    = module.vpc.private_subnet_ids
  eks_security_group = module.eks.node_security_group_id
  db_password        = var.db_password
}
