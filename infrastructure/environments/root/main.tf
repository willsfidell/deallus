terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
  }

  # Uncomment after first apply to enable state management
  # backend "s3" {
  #   bucket         = "deallus-tfstate-root-<ACCOUNT_ID>"
  #   key            = "root/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "deallus-tfstate-lock-root"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "deallus"
      Environment = "root"
      ManagedBy   = "terraform"
    }
  }
}

module "root_account" {
  source = "../../modules/root-account"

  domain_name = var.domain_name
  client_ids  = var.client_ids
}
