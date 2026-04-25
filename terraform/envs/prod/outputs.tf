output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "ecr_urls" {
  description = "ECR repository URLs"
  value       = module.ecr.repository_urls
}

output "rds_endpoint" {
  description = "RDS endpoint (use in DATABASE_URL)"
  value       = module.rds.endpoint
  sensitive   = true
}

output "rds_port" {
  value = module.rds.port
}

output "s3_bucket_name" {
  description = "S3 bucket for hotel images"
  value       = module.s3.bucket_name
}

output "s3_bucket_url" {
  description = "Base URL for hotel images"
  value       = module.s3.bucket_url
}

output "configure_kubectl" {
  description = "Run this command to configure kubectl"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}
