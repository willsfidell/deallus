variable "root_zone_id" {
  description = "Route53 zone ID of the root domain"
  type        = string
}

variable "root_zone_name" {
  description = "Route53 zone name of the root domain (e.g., deallus.ai)"
  type        = string
}

variable "subdomain_prefix" {
  description = "Prefix for the client subdomain (e.g., client1)"
  type        = string
}

variable "client_account_id" {
  description = "AWS account ID of the client (for future use)"
  type        = string
}
