output "hosted_zone_id" {
  description = "Route53 hosted zone ID"
  value       = module.root_account.hosted_zone_id
}

output "name_servers" {
  description = "Nameservers for the root domain"
  value       = module.root_account.name_servers
}

output "state_buckets" {
  description = "S3 state bucket names"
  value       = module.root_account.state_buckets
}

output "lock_tables" {
  description = "DynamoDB lock table names"
  value       = module.root_account.lock_tables
}
