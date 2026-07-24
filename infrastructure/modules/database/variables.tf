variable "identifier" {
  description = "Unique identifier for the RDS instance"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for the database"
  type        = list(string)
}

variable "instance_class" {
  description = "Instance class for the RDS instance"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "database_name" {
  description = "Name of the default database"
  type        = string
  default     = "deallus"
}

variable "master_username" {
  description = "Master username for the database"
  type        = string
  default     = "deallus_admin"
  sensitive   = true
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying the database"
  type        = bool
  default     = false
}

variable "kms_key_id" {
  description = "ARN or ID of KMS key for database encryption (optional, uses AWS managed key by default)"
  type        = string
  default     = null
}
