output "endpoint" {
  description = "The endpoint address of the Redis cluster"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}

output "port" {
  description = "The port of the Redis cluster"
  value       = aws_elasticache_cluster.main.cache_nodes[0].port
}

output "cluster_id" {
  description = "The cluster ID"
  value       = aws_elasticache_cluster.main.cluster_id
}

output "configuration_endpoint" {
  description = "Configuration endpoint for the cluster"
  value       = aws_elasticache_cluster.main.cache_nodes[0].address
}
