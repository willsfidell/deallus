terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.56"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.31"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # Uncomment after first apply
  # backend "s3" {
  #   bucket         = "deallus-tfstate-<CLIENT_ID>-<ACCOUNT_ID>"
  #   key            = "terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "deallus-tfstate-lock-<CLIENT_ID>"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "deallus"
      Environment = var.client_id
      ClientID    = var.client_id
      ManagedBy   = "terraform"
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_id
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  project_name           = var.client_id
  vpc_cidr               = var.vpc_cidr
  availability_zones     = var.availability_zones
  nat_instance_type      = var.nat_instance_type
}

# EKS Module
module "eks" {
  source = "../../modules/eks"

  cluster_name                  = "deallus-${var.client_id}"
  cluster_version               = var.kubernetes_version
  public_subnet_ids             = module.networking.public_subnet_ids
  private_subnet_ids            = module.networking.private_subnet_ids
  orchestrator_instance_type    = var.orchestrator_instance_type
  orchestrator_desired_size     = var.orchestrator_desired_size
  orchestrator_min_size         = var.orchestrator_min_size
  orchestrator_max_size         = var.orchestrator_max_size
  gpu_instance_type             = var.gpu_instance_type
  gpu_desired_size              = var.gpu_desired_size
  gpu_min_size                  = var.gpu_min_size
  gpu_max_size                  = var.gpu_max_size
  gpu_use_spot                  = var.gpu_use_spot
}

# Database Module
module "database" {
  source = "../../modules/database"

  identifier         = "deallus-${var.client_id}"
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.security_groups.rds]
  instance_class     = var.db_instance_class
  allocated_storage  = var.db_allocated_storage
  database_name      = var.database_name
  master_username    = var.master_username
  multi_az           = var.db_multi_az
  kms_key_id         = var.db_kms_key_id
}

# Cache Module
module "cache" {
  source = "../../modules/cache"

  cluster_id         = "deallus-${var.client_id}"
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.security_groups.redis]
  node_type          = var.redis_node_type
  num_cache_nodes    = var.redis_num_nodes
}

# Storage Module
module "storage" {
  source = "../../modules/storage"

  file_system_name   = "deallus-${var.client_id}-models"
  subnet_ids         = module.networking.private_subnet_ids
  security_group_ids = [module.networking.security_groups.efs]
}

# DNS Module
module "dns" {
  source = "../../modules/dns"

  root_zone_id      = var.root_zone_id
  root_zone_name    = var.root_zone_name
  subdomain_prefix  = var.client_id
  client_account_id = var.client_account_id
}
