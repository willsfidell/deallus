terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
  }
}

# EFS File System
resource "aws_efs_file_system" "main" {
  creation_token            = var.file_system_name
  performance_mode          = "generalPurpose"
  throughput_mode           = "bursting"
  encrypted                 = true
  enable_automatic_backups  = true

  tags = {
    Name = var.file_system_name
  }
}

# EFS Mount Targets (one per AZ)
resource "aws_efs_mount_target" "main" {
  count           = length(var.subnet_ids)
  file_system_id  = aws_efs_file_system.main.id
  subnet_id       = var.subnet_ids[count.index]
  security_groups = var.security_group_ids

  tags = {
    Name = "${var.file_system_name}-mount-${count.index + 1}"
  }
}

# EFS Access Point for Ollama models
resource "aws_efs_access_point" "ollama" {
  file_system_id = aws_efs_file_system.main.id
  root_directory {
    path = "/ollama-models"
    creation_info {
      owner_gid   = 1000
      owner_uid   = 1000
      permissions = "755"
    }
  }

  posix_user {
    gid = 1000
    uid = 1000
  }

  tags = {
    Name = "${var.file_system_name}-ollama"
  }
}

# CloudWatch Log Group for EFS
resource "aws_cloudwatch_log_group" "efs" {
  name              = "/aws/efs/${var.file_system_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.file_system_name}-logs"
  }
}

# EFS Backup Policy
resource "aws_efs_backup_policy" "main" {
  file_system_id = aws_efs_file_system.main.id

  backup_policy {
    status = "ENABLED"
  }
}
