output "endpoint" {
  description = "The endpoint of the database"
  value       = aws_db_instance.main.endpoint
}

output "address" {
  description = "The hostname of the database"
  value       = aws_db_instance.main.address
}

output "port" {
  description = "The port of the database"
  value       = aws_db_instance.main.port
}

output "database_name" {
  description = "The name of the default database"
  value       = aws_db_instance.main.db_name
}

output "master_username" {
  description = "The master username for the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "password_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the database password"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "connection_string_secret_arn" {
  description = "ARN of the Secrets Manager secret containing the full connection string"
  value       = aws_secretsmanager_secret.db_connection.arn
}

output "security_group_id" {
  description = "Security group ID of the database"
  value       = aws_db_instance.main.db_security_groups[0] != "" ? aws_db_instance.main.db_security_groups[0] : "default"
}
