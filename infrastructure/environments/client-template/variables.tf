variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "client_id" {
  description = "Client identifier"
  type        = string
}

variable "client_account_id" {
  description = "AWS account ID where the client infrastructure will be deployed"
  type        = string
}

variable "root_zone_id" {
  description = "Route53 zone ID of the root domain"
  type        = string
}

variable "root_zone_name" {
  description = "Root domain name (e.g., deallus.ai)"
  type        = string
  default     = "deallus.ai"
}

# Networking
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "nat_instance_type" {
  description = "EC2 instance type for NAT instances"
  type        = string
  default     = "t4g.nano"
}

# EKS
variable "kubernetes_version" {
  description = "Kubernetes version"
  type        = string
  default     = "1.28"
}

variable "orchestrator_instance_type" {
  description = "Instance type for orchestrator nodes"
  type        = string
  default     = "t3.small"
}

variable "orchestrator_desired_size" {
  description = "Desired number of orchestrator nodes"
  type        = number
  default     = 2
}

variable "orchestrator_min_size" {
  description = "Minimum number of orchestrator nodes"
  type        = number
  default     = 2
}

variable "orchestrator_max_size" {
  description = "Maximum number of orchestrator nodes"
  type        = number
  default     = 4
}

variable "gpu_instance_type" {
  description = "Instance type for GPU nodes"
  type        = string
  default     = "g4dn.xlarge"
}

variable "gpu_desired_size" {
  description = "Desired number of GPU nodes"
  type        = number
  default     = 1
}

variable "gpu_min_size" {
  description = "Minimum number of GPU nodes"
  type        = number
  default     = 1
}

variable "gpu_max_size" {
  description = "Maximum number of GPU nodes"
  type        = number
  default     = 3
}

variable "gpu_use_spot" {
  description = "Use spot instances for GPU nodes"
  type        = bool
  default     = true
}

# Database
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "database_name" {
  description = "Database name"
  type        = string
  default     = "deallus"
}

variable "master_username" {
  description = "Master database username"
  type        = string
  default     = "deallus_admin"
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

variable "db_kms_key_id" {
  description = "KMS key ID or ARN for RDS encryption (optional, uses AWS managed key by default)"
  type        = string
  default     = null
}

# Cache
variable "redis_node_type" {
  description = "Redis node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_nodes" {
  description = "Number of Redis nodes"
  type        = number
  default     = 1
}
