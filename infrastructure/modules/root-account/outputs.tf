output "hosted_zone_id" {
  description = "Route53 hosted zone ID for the root domain"
  value       = aws_route53_zone.root.zone_id
}

output "name_servers" {
  description = "Nameservers for the root hosted zone"
  value       = aws_route53_zone.root.name_servers
}

output "state_buckets" {
  description = "Map of client IDs to S3 state bucket names"
  value = {
    root = aws_s3_bucket.root_state.bucket
    clients = {
      for k, v in aws_s3_bucket.client_state : k => v.bucket
    }
  }
}

output "lock_tables" {
  description = "Map of DynamoDB lock table names"
  value = {
    root = aws_dynamodb_table.root_lock.name
    clients = {
      for k, v in aws_dynamodb_table.client_lock : k => v.name
    }
  }
}
