output "client_id" {
  description = "Client identifier"
  value       = var.client_id
}

output "subdomain" {
  description = "Client subdomain"
  value       = module.dns.subdomain
}

output "eks_cluster_id" {
  description = "EKS cluster ID"
  value       = module.eks.cluster_id
}

output "eks_cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = module.database.endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.cache.endpoint
}

output "efs_file_system_id" {
  description = "EFS file system ID"
  value       = module.storage.file_system_id
}

output "efs_access_point_id" {
  description = "EFS access point ID for Ollama models"
  value       = module.storage.access_point_id
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.networking.vpc_id
}

output "configure_kubectl_command" {
  description = "Command to configure kubectl"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_id} --region ${var.aws_region}"
}
