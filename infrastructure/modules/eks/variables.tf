variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "cluster_version" {
  description = "Kubernetes version to use for the EKS cluster"
  type        = string
  default     = "1.28"
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "orchestrator_instance_type" {
  description = "EC2 instance type for orchestrator nodes"
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
  description = "EC2 instance type for GPU nodes"
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
  description = "Use spot instances for GPU nodes (cost optimization)"
  type        = bool
  default     = true
}
