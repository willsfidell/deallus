terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
  }
}

# RDS DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.identifier}-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.identifier}-db-subnet-group"
  }
}

# Create Secrets Manager secret for database password
# This secret will be automatically managed and rotated by RDS
resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${var.identifier}-password"
  description             = "RDS master password for ${var.identifier}"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.identifier}-password"
  }
}

# Generate initial password
resource "random_password" "db_password" {
  length  = 32
  special = true
}

# Set initial secret version
resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = random_password.db_password.result
}

# RDS PostgreSQL Instance
# Password managed by AWS Secrets Manager with automatic rotation
resource "aws_db_instance" "main" {
  identifier     = var.identifier
  engine         = "postgres"
  engine_version = "16.3"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_id

  db_name  = var.database_name
  username = var.master_username
  password = aws_secretsmanager_secret_version.db_password.secret_string

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids

  multi_az               = var.multi_az
  publicly_accessible    = false
  skip_final_snapshot    = var.skip_final_snapshot
  copy_tags_to_snapshot  = true

  backup_retention_period = 7
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  enabled_cloudwatch_logs_exports = ["postgresql"]
  enable_iam_database_authentication = true

  # Enable performance insights
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  tags = {
    Name = var.identifier
  }

  depends_on = [aws_secretsmanager_secret_version.db_password]
}

# Attach RDS secret target for automatic rotation
resource "aws_secretsmanager_secret_target_attachment" "db_password" {
  secret_id      = aws_secretsmanager_secret.db_password.id
  target_id      = aws_db_instance.main.resource_id
  target_type    = "RDS"
}

# Configure automatic rotation for the secret
resource "aws_secretsmanager_secret_rotation" "db_password" {
  secret_id           = aws_secretsmanager_secret.db_password.id
  rotation_enabled    = true
  rotation_rules {
    automatically_after_days = 30
  }

  depends_on = [aws_secretsmanager_secret_target_attachment.db_password]
}

# Store connection string in Secrets Manager (separate from password)
resource "aws_secretsmanager_secret" "db_connection" {
  name                    = "${var.identifier}-connection"
  description             = "RDS connection details for ${var.identifier}"
  recovery_window_in_days = 7

  tags = {
    Name = "${var.identifier}-connection"
  }
}

resource "aws_secretsmanager_secret_version" "db_connection" {
  secret_id = aws_secretsmanager_secret.db_connection.id
  secret_string = jsonencode({
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    database = aws_db_instance.main.db_name
    username = aws_db_instance.main.username
    password = aws_secretsmanager_secret_version.db_password.secret_string
    engine   = "postgresql"
    dbname   = aws_db_instance.main.db_name
  })

  depends_on = [aws_secretsmanager_secret_version.db_password]
}
