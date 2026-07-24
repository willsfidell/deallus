terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Generate random suffix for subdomain
resource "random_string" "subdomain_suffix" {
  length  = 5
  lower   = true
  numeric = false
  upper   = false
  special = false
}

# Local subdomain name
locals {
  full_subdomain = "${var.subdomain_prefix}-${random_string.subdomain_suffix.result}-node.${var.root_zone_name}"
}

# Route53 Hosted Zone for client subdomain
resource "aws_route53_zone" "client" {
  name = local.full_subdomain

  tags = {
    Name = local.full_subdomain
  }
}

# NS records in root zone pointing to client zone nameservers
resource "aws_route53_record" "delegation" {
  zone_id = var.root_zone_id
  name    = local.full_subdomain
  type    = "NS"
  ttl     = 300

  records = aws_route53_zone.client.name_servers
}

# A record placeholder (will be created by Ingress)
# This is just a placeholder for future ALB integration
resource "aws_route53_record" "alb_placeholder" {
  zone_id = aws_route53_zone.client.zone_id
  name    = local.full_subdomain
  type    = "A"
  ttl     = 300
  records = ["127.0.0.1"]

  lifecycle {
    ignore_changes = [records]
  }
}
