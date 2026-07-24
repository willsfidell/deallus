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

variable "project_name" {
  description = "Project name for tagging"
  type        = string
}
