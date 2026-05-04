variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project name used for resource naming"
  type        = string
  default     = "travelhub"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "cluster_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.35"
}

# ── Sensitive ── passed via TF_VAR_* env vars in CI/CD, never in tfvars ────────────
variable "db_password" {
  description = "RDS master password — set via TF_VAR_db_password"
  type        = string
  sensitive   = true
}

variable "jwt_secret" {
  description = "JWT signing secret — set via TF_VAR_jwt_secret"
  type        = string
  sensitive   = true
}

variable "aes_encryption_key" {
  description = "AES-256 key for pgcrypto — set via TF_VAR_aes_encryption_key"
  type        = string
  sensitive   = true
}

variable "internal_api_key" {
  description = "Internal service-to-service API key — set via TF_VAR_internal_api_key"
  type        = string
  sensitive   = true
}
