variable "domain_name" {
  description = "Base domain name for Route53 (e.g., deallus.ai)"
  type        = string
}

variable "client_ids" {
  description = "List of client IDs for state bucket creation"
  type        = list(string)
  default     = []
}
