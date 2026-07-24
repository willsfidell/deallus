# Deallus Infrastructure

Complete multi-tenant AWS infrastructure-as-code for the Deallus AI orchestrator platform using OpenTofu, Helm, and Kubernetes.

**Status:** Production-ready template for POC and scaling  
**Last Updated:** January 28, 2025

## ✨ Features

- **Multi-tenant Architecture**: Complete isolation per client with per-client AWS accounts
- **Infrastructure as Code**: OpenTofu (Terraform OSS fork) for reproducible deployments
- **Kubernetes-native**: EKS + Helm for application deployment and scaling
- **Cost-optimized**: Spot instances for GPU, t4g.nano NAT instances, RDS db.t3.micro
- **GPU Support**: g4dn.xlarge instances with pre-loaded Ollama models
- **Automated Provisioning**: CLI scripts for client onboarding and management
- **Comprehensive Monitoring**: AWS CloudWatch integration with EFS, RDS, and application logs

## 🏗 Architecture Overview

```
┌─────────────────────────────────────────┐
│         Root AWS Account                │
│  Route53 (deallus.ai) - Central DNS    │
│  S3 State Buckets (one per client)     │
│  DynamoDB Lock Tables (state locking)  │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
Client1      Client2    Client3
(Account A) (Account B) (Account C)
    │          │          │
    ▼          ▼          ▼
┌─────────────────────────────────────┐
│      VPC (10.0.0.0/16)              │
│  ┌───────────────────────────────┐  │
│  │  EKS Cluster                  │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ Orchestrator Nodes (x2) │  │  │
│  │  │   t3.small, On-Demand   │  │  │
│  │  └─────────────────────────┘  │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │ GPU Nodes (x1)          │  │  │
│  │  │ g4dn.xlarge, Spot       │  │  │
│  │  │ (with Ollama)           │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
│                                     │
│  RDS PostgreSQL db.t3.micro        │
│  ElastiCache Redis cache.t3.micro  │
│  EFS for Ollama Models             │
└─────────────────────────────────────┘
```

## 📁 Directory Structure

```
infrastructure/
├── versions.tf              # Provider version constraints
├── .gitignore              # Ignore state files, secrets
├── .editorconfig           # Code formatting rules
│
├── modules/                # Reusable Terraform modules
│   ├── root-account/       # Route53, S3 state, DynamoDB locks
│   ├── networking/         # VPC, subnets, NAT, security groups
│   ├── eks/               # EKS cluster, node groups, addons
│   ├── database/          # RDS PostgreSQL
│   ├── cache/             # ElastiCache Redis
│   ├── storage/           # EFS for models
│   └── dns/               # Route53 subdomains, NS delegation
│
├── environments/           # Environment-specific configs
│   ├── root/              # Root account (one-time setup)
│   ├── client-template/   # Template for new clients
│   └── client1/           # Example client1 configuration
│
├── helm/                   # Helm charts
│   ├── deallus-orchestrator/  # Backend API chart
│   ├── ollama/                # GPU workload chart
│   └── infrastructure/        # K8s add-ons (future)
│
├── scripts/                # Automation scripts
│   ├── create-client.sh        # Provision new client
│   ├── destroy-client.sh       # Tear down client
│   ├── apply-helm.sh           # Deploy Helm charts
│   └── emergency-migrate.sh    # Manual DB migrations
│
└── docs/                   # Documentation
    ├── README.md           # This file
    ├── setup.md            # Initial setup guide
    ├── architecture.md     # Detailed architecture
    ├── provisioning.md     # Client provisioning guide
    └── troubleshooting.md  # Common issues & solutions
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install required tools
brew install opentofu helm kubectl awscli
```

### 2. Setup Root Account (One-time)

```bash
cd environments/root

# Copy and edit terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit: domain_name = "deallus.ai", etc.

# Initialize and apply
tofu init
tofu plan -out=tfplan
tofu apply tfplan

# Note the outputs:
# - hosted_zone_id (save this!)
# - name_servers (configure registrar)
```

### 3. Provision First Client

```bash
# Create client environment
./scripts/create-client.sh client1 123456789012 us-east-1

cd environments/client1

# Edit terraform.tfvars with Route53 zone ID
vim terraform.tfvars

# Deploy
tofu init
tofu plan -out=tfplan
tofu apply tfplan

# Configure kubectl
aws eks update-kubeconfig --name deallus-client1 --region us-east-1

# Verify cluster
kubectl get nodes
```

## 📊 Cost Estimate (Monthly per Client - POC)

| Component | Instance | Hours/Month | Cost |
|-----------|----------|-------------|------|
| EKS Cluster Control Plane | - | - | $73 |
| Orchestrator Nodes | t3.small (2x) | 730 | $62 |
| GPU Nodes | g4dn.xlarge (Spot) | 730 | $77 |
| RDS PostgreSQL | db.t3.micro | 730 | $15 |
| ElastiCache Redis | cache.t3.micro | 730 | $10 |
| EFS Storage | 100GB | - | $30 |
| Data Transfer | Outbound | - | $5 |
| **Total** | | | **~$272/month** |

## 🔒 Security Features

- ✅ VPC with private subnets for data services
- ✅ NAT instances for outbound traffic control
- ✅ Security groups per service (RDS, Redis, EFS)
- ✅ Encryption in-transit (TLS via cert-manager)
- ✅ Encryption at-rest (EBS, RDS, EFS, S3)
- ✅ IAM roles with least-privilege (IRSA for pod auth)
- ✅ Secrets Manager for database credentials
- ✅ S3 bucket versioning and MFA delete protection
- ✅ Terraform state encryption and locking

## 🛠 Common Tasks

### Deploy Application to Cluster

```bash
# Update Helm values as needed
vim helm/deallus-orchestrator/values.yaml

# Deploy backend
./scripts/apply-helm.sh client1 deallus-orchestrator

# Deploy Ollama GPU workload
./scripts/apply-helm.sh client1 ollama

# Check status
kubectl get pods -n deallus
```

### Run Database Migrations

```bash
# Automatic (init job)
# Already runs on Helm chart deployment

# Manual (if init job fails)
./scripts/emergency-migrate.sh client1
```

### Access Database

```bash
# Get connection string
aws secretsmanager get-secret-value \
  --secret-id deallus-client1-connection \
  --query SecretString \
  --output text | jq .

# Connect via AWS Systems Manager
aws ssm start-session --target i-1234567890abcdef0
psql -h deallus-client1.xxxxx.us-east-1.rds.amazonaws.com -U deallus_admin -d deallus
```

### Scale Cluster

```bash
cd environments/client1

# Edit terraform.tfvars
vim terraform.tfvars
# Change: orchestrator_desired_size = 4, gpu_desired_size = 2

# Apply changes
tofu apply
```

### Destroy Client Infrastructure

```bash
# DESTRUCTIVE - Will delete all resources!
./scripts/destroy-client.sh client1
```

## 📖 Documentation

- **[setup.md](docs/setup.md)** - Detailed setup instructions
- **[architecture.md](docs/architecture.md)** - In-depth architecture diagrams and decisions
- **[provisioning.md](docs/provisioning.md)** - Adding new clients
- **[troubleshooting.md](docs/troubleshooting.md)** - Common issues and solutions

## 🤝 Contributing

When modifying infrastructure:

1. Update relevant module variables/outputs
2. Test with `tofu plan` before applying
3. Update documentation
4. Tag releases with version numbers

## 📝 Notes

### State Management

- **Root account**: Local S3 backend (created manually first time)
- **Client accounts**: Separate S3 bucket + DynamoDB per client
- **Locking**: DynamoDB prevents concurrent modifications
- **Backups**: S3 versioning enabled automatically

### Networking

- **NAT Instances**: Running instances in public subnets (one per AZ for HA)
- **EKS Service IPs**: Automatically assigned from VPC CIDR
- **Load Balancer**: AWS ALB via Kubernetes ingress controller (deployed via Helm)

### Scaling Recommendations

- **Orchestrator nodes**: 2-4 for POC, scale to 5+ for production
- **GPU nodes**: Start with 1, scale to 3-5 depending on inference load
- **Database**: Switch to db.t3.small → db.t3.medium for production
- **Redis**: Add replicas for HA in production

## 🔗 Related Documentation

- [Deallus Backend](../backend/) - FastAPI orchestrator
- [Model System](../CREATING_MODELS.md) - Creating custom models
- [API Documentation](../CURL_COMMANDS.md) - API endpoint reference

---

**Questions?** Check [troubleshooting.md](docs/troubleshooting.md) or review Terraform code in `modules/`.
