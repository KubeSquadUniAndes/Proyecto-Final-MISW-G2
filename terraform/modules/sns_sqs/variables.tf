variable "project" {
  description = "Project name prefix used in all resource names and tags"
  type        = string
  nullable    = false
}

variable "environment" {
  description = "Deployment environment (e.g. prod, staging, dev)"
  type        = string
  nullable    = false

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod."
  }
}

variable "node_role_name" {
  description = "Name of the EKS node IAM role to attach SNS publish and SQS consume policies to"
  type        = string
  nullable    = false
}

variable "oidc_provider_arn" {
  description = "ARN of the EKS OIDC provider — required for IRSA trust policies"
  type        = string
  nullable    = false
}

variable "oidc_provider_url" {
  description = "EKS OIDC provider URL without https:// (e.g. oidc.eks.us-east-1.amazonaws.com/id/XXXX)"
  type        = string
  nullable    = false
}

variable "visibility_timeout_seconds" {
  description = "Seconds a received message is hidden from other consumers; must be >= consumer max processing time"
  type        = number
  default     = 60
  nullable    = false

  validation {
    condition     = var.visibility_timeout_seconds >= 30 && var.visibility_timeout_seconds <= 43200
    error_message = "visibility_timeout_seconds must be between 30 and 43200."
  }
}

variable "message_retention_seconds" {
  description = "Seconds SQS retains an unprocessed message before discarding it"
  type        = number
  default     = 86400 # 24 hours — enough for a transient hospedajes_ms outage
  nullable    = false

  validation {
    condition     = var.message_retention_seconds >= 60 && var.message_retention_seconds <= 1209600
    error_message = "message_retention_seconds must be between 60 (1 min) and 1209600 (14 days)."
  }
}

variable "max_receive_count" {
  description = "Times a message is delivered before being moved to the dead-letter queue"
  type        = number
  default     = 3
  nullable    = false

  validation {
    condition     = var.max_receive_count >= 1 && var.max_receive_count <= 1000
    error_message = "max_receive_count must be between 1 and 1000."
  }
}
