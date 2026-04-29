output "cluster_name" {
  value = aws_eks_cluster.main.name
}

output "cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}

output "cluster_ca" {
  value = aws_eks_cluster.main.certificate_authority[0].data
}

output "node_security_group_id" {
  value = aws_security_group.eks_nodes.id
}

output "cluster_security_group_id" {
  value = aws_eks_cluster.main.vpc_config[0].cluster_security_group_id
}

output "external_secrets_role_arn" {
  value       = aws_iam_role.external_secrets.arn
  description = "IAM Role ARN for External Secrets Operator (IRSA)"
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.eks.arn
}
output "node_role_name" {
  value = aws_iam_role.eks_nodes.name
}
