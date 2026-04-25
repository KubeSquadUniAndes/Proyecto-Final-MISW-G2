terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

data "aws_caller_identity" "current" {}

# ── S3 Bucket ─────────────────────────────────────────────────────────────────
resource "aws_s3_bucket" "images" {
  bucket = "travelhub-images-${data.aws_caller_identity.current.account_id}"

  tags = {
    Project     = "travelhub"
    Environment = "prod"
  }
}

resource "aws_s3_bucket_cors_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST"]
    allowed_origins = ["*"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

resource "aws_s3_bucket_policy" "public_read" {
  bucket     = aws_s3_bucket.images.id
  depends_on = [aws_s3_bucket_public_access_block.images]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "PublicReadGetObject"
      Effect    = "Allow"
      Principal = "*"
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.images.arn}/*"
    }]
  })
}

# ── IAM: permite a los nodos EKS subir y borrar imágenes ─────────────────────
resource "aws_iam_policy" "s3_images_rw" {
  name        = "travelhub-prod-s3-images-rw"
  description = "Allow hospedajes_ms pods to upload and delete hotel images"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:PutObject", "s3:DeleteObject"]
      Resource = "${aws_s3_bucket.images.arn}/*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "nodes_s3_images" {
  # Nombre del node role que ya existe en EKS
  role       = "travelhub-prod-eks-node-role"
  policy_arn = aws_iam_policy.s3_images_rw.arn
}

# ── Outputs ───────────────────────────────────────────────────────────────────
output "bucket_name" {
  value = aws_s3_bucket.images.id
}

output "bucket_url" {
  value = "https://${aws_s3_bucket.images.bucket_regional_domain_name}"
}
