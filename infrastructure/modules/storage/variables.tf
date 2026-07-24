variable "file_system_name" {
  description = "Name of the EFS file system"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for mount targets"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for mount targets"
  type        = list(string)
}
