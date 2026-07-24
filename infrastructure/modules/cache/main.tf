terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
  }
}

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.cluster_id}-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.cluster_id}-subnet-group"
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_cluster" "main" {
  cluster_id           = var.cluster_id
  engine               = "redis"
  node_type            = var.node_type
  num_cache_nodes      = var.num_cache_nodes
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = var.security_group_ids
  automatic_failover_enabled = false

  at_rest_encryption_enabled = true
  transit_encryption_enabled = false

  log_delivery_configuration {
    destination      = "cloudwatch-logs"
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }

  tags = {
    Name = var.cluster_id
  }
}

# ElastiCache Parameter Group for Redis 7 (if custom parameters needed in future)
resource "aws_elasticache_parameter_group" "custom" {
  family      = "redis7"
  name        = "${var.cluster_id}-param-group"
  description = "Parameter group for ${var.cluster_id}"

  tags = {
    Name = "${var.cluster_id}-param-group"
  }
}
