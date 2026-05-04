variable "project" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "eks_security_group" {
  type        = string
  description = "Custom EKS node security group"
}
variable "eks_cluster_security_group" {
  type        = string
  description = "EKS auto-created cluster security group (used by managed node groups)"
}
variable "db_password" {
  type      = string
  sensitive = true
  description = "RDS master password — passed from secrets module output"
}

# ── Subnet Group ──────────────────────────────────────────────────────────────
resource "aws_db_subnet_group" "main" {
  name       = "${var.project}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnets
  tags       = { Name = "${var.project}-${var.environment}-db-subnet-group" }
}

# ── Security Group ────────────────────────────────────────────────────────────
resource "aws_security_group" "rds" {
  name        = "${var.project}-${var.environment}-rds-sg"
  description = "Allow PostgreSQL from EKS nodes"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.eks_security_group, var.eks_cluster_security_group]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.environment}-rds-sg" }
}

# ── RDS Instance ──────────────────────────────────────────────────────────────
resource "aws_db_instance" "main" {
  identifier     = "${var.project}-${var.environment}-postgres"
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 30  # reduced from 100 — sufficient for this workload
  storage_encrypted     = true

  db_name  = "postgres"
  username = "postgres"
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az               = false
  publicly_accessible    = false
  deletion_protection    = true
  skip_final_snapshot    = false
  final_snapshot_identifier = "${var.project}-${var.environment}-final-snapshot"

  backup_retention_period = 1  # reduced from 7 — academic environment
  backup_window           = "03:00-04:00"
  maintenance_window      = "Mon:04:00-Mon:05:00"

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# ── Databases ─────────────────────────────────────────────────────────────────
# Creates all required databases via a provisioner after RDS is ready.
# Uses a null_resource so databases are idempotent (CREATE IF NOT EXISTS).
resource "null_resource" "create_databases" {
  depends_on = [aws_db_instance.main]

  provisioner "local-exec" {
    command = <<-EOT
      export PGPASSWORD='${var.db_password}'
      for db in bookings_db auth_db users_db anomalies_db hospedajes_db; do
        psql -h ${aws_db_instance.main.address} -U postgres -tc \
          "SELECT 1 FROM pg_database WHERE datname = '$db'" | grep -q 1 || \
          psql -h ${aws_db_instance.main.address} -U postgres -c "CREATE DATABASE $db;"
      done
      psql -h ${aws_db_instance.main.address} -U postgres -d bookings_db \
        -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
    EOT
  }

  triggers = {
    rds_id = aws_db_instance.main.id
  }
}

output "endpoint" {
  value     = aws_db_instance.main.endpoint
  sensitive = true
}

output "address" {
  value     = aws_db_instance.main.address
  sensitive = true
}

output "port" {
  value = aws_db_instance.main.port
}

output "username" {
  value = aws_db_instance.main.username
}
