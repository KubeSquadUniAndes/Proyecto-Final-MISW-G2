variable "project" { type = string }
variable "environment" { type = string }

variable "db_password" {
  type      = string
  sensitive = true
}

variable "jwt_secret" {
  type      = string
  sensitive = true
}

variable "aes_encryption_key" {
  type      = string
  sensitive = true
}

variable "internal_api_key" {
  type      = string
  sensitive = true
}

# ── RDS password ──────────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "rds_password" {
  name                    = "travelhub/rds/password"
  description             = "RDS PostgreSQL master password"
  recovery_window_in_days = 7

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "rds_password" {
  secret_id     = aws_secretsmanager_secret.rds_password.id
  secret_string = var.db_password
}

# ── JWT secret ────────────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "jwt_secret" {
  name                    = "travelhub/app/jwt-secret"
  description             = "JWT signing secret shared across microservices"
  recovery_window_in_days = 7

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret
}

# ── AES encryption key (reservas_ms pgcrypto) ─────────────────────────────────
resource "aws_secretsmanager_secret" "aes_encryption_key" {
  name                    = "travelhub/reservas/aes-key"
  description             = "AES-256 key for pgcrypto encryption of traveler sensitive fields"
  recovery_window_in_days = 7

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "aes_encryption_key" {
  secret_id     = aws_secretsmanager_secret.aes_encryption_key.id
  secret_string = var.aes_encryption_key
}

# ── Internal API key ──────────────────────────────────────────────────────────
resource "aws_secretsmanager_secret" "internal_api_key" {
  name                    = "travelhub/app/internal-api-key"
  description             = "Internal API key for service-to-service communication"
  recovery_window_in_days = 7

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "internal_api_key" {
  secret_id     = aws_secretsmanager_secret.internal_api_key.id
  secret_string = var.internal_api_key
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "rds_password_arn" {
  value = aws_secretsmanager_secret.rds_password.arn
}

output "jwt_secret_arn" {
  value = aws_secretsmanager_secret.jwt_secret.arn
}

output "aes_key_arn" {
  value = aws_secretsmanager_secret.aes_encryption_key.arn
}

output "internal_api_key_arn" {
  value = aws_secretsmanager_secret.internal_api_key.arn
}
