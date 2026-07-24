output "subdomain" {
  description = "Full subdomain for the client"
  value       = local.full_subdomain
}

output "subdomain_zone_id" {
  description = "Route53 zone ID for the client subdomain"
  value       = aws_route53_zone.client.zone_id
}

output "subdomain_name_servers" {
  description = "Nameservers for the client subdomain"
  value       = aws_route53_zone.client.name_servers
}

output "random_suffix" {
  description = "Random suffix used in subdomain"
  value       = random_string.subdomain_suffix.result
}
