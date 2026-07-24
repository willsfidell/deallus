terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
  }
}

# Route53 hosted zone
resource "aws_route53_zone" "root" {
  name = var.domain_name

  tags = {
    Name    = "deallus-root-zone"
    Project = "deallus"
  }
}

# S3 bucket for root account state
resource "aws_s3_bucket" "root_state" {
  bucket = "deallus-tfstate-root-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name    = "deallus-root-state"
    Project = "deallus"
  }
}

# S3 buckets for each client state
resource "aws_s3_bucket" "client_state" {
  for_each = toset(var.client_ids)

  bucket = "deallus-tfstate-${each.value}-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name    = "deallus-${each.value}-state"
    Project = "deallus"
  }
}

# Enable versioning for root state bucket
resource "aws_s3_bucket_versioning" "root_state" {
  bucket = aws_s3_bucket.root_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable versioning for client state buckets
resource "aws_s3_bucket_versioning" "client_state" {
  for_each = aws_s3_bucket.client_state

  bucket = each.value.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable encryption for root state bucket
resource "aws_s3_bucket_server_side_encryption_configuration" "root_state" {
  bucket = aws_s3_bucket.root_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Enable encryption for client state buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "client_state" {
  for_each = aws_s3_bucket.client_state

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DynamoDB table for root state locking
resource "aws_dynamodb_table" "root_lock" {
  name           = "deallus-tfstate-lock-root"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name    = "deallus-root-lock"
    Project = "deallus"
  }
}

# DynamoDB tables for client state locking
resource "aws_dynamodb_table" "client_lock" {
  for_each = toset(var.client_ids)

  name           = "deallus-tfstate-lock-${each.value}"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name    = "deallus-${each.value}-lock"
    Project = "deallus"
  }
}

# Block public access to state buckets
resource "aws_s3_bucket_public_access_block" "root_state" {
  bucket = aws_s3_bucket.root_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "client_state" {
  for_each = aws_s3_bucket.client_state

  bucket = each.value.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Data source to get current AWS account
data "aws_caller_identity" "current" {}
