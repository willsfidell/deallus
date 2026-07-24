variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Root domain name for Route53"
  type        = string
}

variable "client_ids" {
  description = "List of client IDs to pre-create S3 buckets for"
  type        = list(string)
  default     = ["client1"]
}
