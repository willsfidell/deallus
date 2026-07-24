output "file_system_id" {
  description = "EFS file system ID"
  value       = aws_efs_file_system.main.id
}

output "file_system_arn" {
  description = "EFS file system ARN"
  value       = aws_efs_file_system.main.arn
}

output "dns_name" {
  description = "EFS DNS name"
  value       = aws_efs_file_system.main.dns_name
}

output "access_point_id" {
  description = "EFS access point ID for Ollama models"
  value       = aws_efs_access_point.ollama.id
}

output "access_point_arn" {
  description = "EFS access point ARN for Ollama models"
  value       = aws_efs_access_point.ollama.arn
}

output "mount_target_ids" {
  description = "List of EFS mount target IDs"
  value       = aws_efs_mount_target.main[*].id
}
