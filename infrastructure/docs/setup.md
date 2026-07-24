# Initial Setup Guide

Complete step-by-step guide to set up the Deallus infrastructure on AWS.

## Prerequisites

### Software

```bash
# macOS
brew install opentofu helm kubectl awscli

# Linux (Ubuntu/Debian)
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install tofu
sudo snap install helm --classic
sudo snap install kubectl --classic
```

### AWS Setup

1. **AWS Account Structure**
   ```
   Root Account: Owns domain (deallus.ai) in Route53
   Client Account 1: Contains EKS, RDS, etc.
   Client Account 2: Contains EKS, RDS, etc.
   ```

2. **Credentials Setup**
   ```bash
   # Configure AWS CLI with root account
   aws configure --profile deallus-root
   
   # Configure CLI with client account
   aws configure --profile deallus-client1
   
   # Export profiles for Terraform
   export AWS_PROFILE=deallus-root
   ```

3. **Domain Registration**
   - Register `deallus.ai` with your registrar (Route53, Namecheap, etc.)
   - We'll configure Route53 nameservers in root account

## Step 1: Root Account Setup (One-time)

### 1.1 Initialize Root Environment

```bash
cd infrastructure/environments/root

# Copy template
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars
```

**terraform.tfvars:**
```hcl
aws_region = "us-east-1"
domain_name = "deallus.ai"
client_ids = ["client1"]  # Pre-create buckets for these clients
```

### 1.2 Create S3 Backend (First Time Only)

Before running `tofu init`, you need to create the S3 bucket manually:

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create S3 bucket
aws s3 mb s3://deallus-tfstate-root-${ACCOUNT_ID} --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket deallus-tfstate-root-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket deallus-tfstate-root-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}
    }]
  }'

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name deallus-tfstate-lock-root \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Wait for table to be created
aws dynamodb wait table-exists \
  --table-name deallus-tfstate-lock-root \
  --region us-east-1
```

### 1.3 Uncomment Backend Configuration

Edit `backend.tf` and replace the placeholder:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
sed -i "s/REPLACE_ACCOUNT_ID/${ACCOUNT_ID}/g" backend.tf
```

### 1.4 Deploy Root Infrastructure

```bash
# Initialize Terraform
tofu init

# Plan changes
tofu plan -out=tfplan

# Apply
tofu apply tfplan

# Save outputs
tofu output > root-outputs.txt
```

**Save these outputs:**
- `hosted_zone_id` - You'll need this for client deployments
- `name_servers` - Configure these with your domain registrar

### 1.5 Configure Domain Nameservers

In your domain registrar's console, update nameservers to the values from `root-outputs.txt`.

**Example (Route53 to external registrar):**
- Name Server 1: ns-1234.awsdns-12.com
- Name Server 2: ns-5678.awsdns-34.co.uk
- etc.

Wait 5-30 minutes for DNS propagation:

```bash
# Verify nameservers
nslookup deallus.ai
# Should show AWS nameservers
```

## Step 2: Client Account Setup

### 2.1 Create Client Environment

```bash
cd infrastructure

# Create new client
./scripts/create-client.sh client1 123456789012 us-east-1

# Navigate to client directory
cd environments/client1
```

### 2.2 Update Client Configuration

```bash
# Edit terraform.tfvars
vim terraform.tfvars
```

**Update these values:**
```hcl
aws_region         = "us-east-1"
client_id          = "client1"
client_account_id  = "123456789012"  # YOUR account ID
root_zone_id       = "Z1A2B3C4D5E6F7"  # From root-outputs.txt
root_zone_name     = "deallus.ai"

# Optional customizations
orchestrator_desired_size = 2
gpu_desired_size          = 1
db_instance_class         = "db.t3.micro"
```

### 2.3 Prepare Client S3 Backend

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --profile deallus-client1 --query Account --output text)
AWS_REGION="us-east-1"

# Create S3 bucket
aws s3 mb s3://deallus-tfstate-client1-${ACCOUNT_ID} \
  --region ${AWS_REGION} \
  --profile deallus-client1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket deallus-tfstate-client1-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled \
  --profile deallus-client1

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name deallus-tfstate-lock-client1 \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ${AWS_REGION} \
  --profile deallus-client1
```

### 2.4 Update Backend Configuration

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --profile deallus-client1 --query Account --output text)
sed -i "s/REPLACE_ACCOUNT_ID/${ACCOUNT_ID}/g" backend.tf
```

### 2.5 Deploy Client Infrastructure

```bash
# Switch to client account profile
export AWS_PROFILE=deallus-client1

# Initialize
tofu init

# Plan (takes 3-5 minutes)
tofu plan -out=tfplan

# Apply (takes 15-25 minutes)
tofu apply tfplan

# Save outputs
tofu output > client-outputs.txt
```

**This will create:**
- VPC with public/private subnets across 3 AZs
- EKS cluster with 2 orchestrator nodes and 1 GPU node
- RDS PostgreSQL instance
- ElastiCache Redis instance
- EFS storage for Ollama models
- Client subdomain (e.g., client1-xyzab-node.deallus.ai)

### 2.6 Configure kubectl

```bash
# Get cluster info from outputs
CLUSTER_NAME=$(tofu output -raw eks_cluster_id)
AWS_REGION="us-east-1"

# Update kubeconfig
aws eks update-kubeconfig \
  --name ${CLUSTER_NAME} \
  --region ${AWS_REGION} \
  --profile deallus-client1

# Verify cluster access
kubectl get nodes
kubectl get pods -A
```

**Expected output:**
```
NAME                          STATUS   ROLES    AGE
ip-10-0-101-10.ec2.internal   Ready    <none>   5m
ip-10-0-102-20.ec2.internal   Ready    <none>   5m
ip-10-0-103-30.ec2.internal   Ready    <gpu>    3m
```

## Step 3: Deploy Applications

### 3.1 Deploy Backend API

```bash
# Navigate to scripts directory
cd infrastructure

# Deploy
./scripts/apply-helm.sh client1 deallus-orchestrator

# Check status
kubectl get pods -n deallus
kubectl get svc -n deallus
kubectl get ingress -n deallus
```

### 3.2 Deploy Ollama GPU Workload

```bash
./scripts/apply-helm.sh client1 ollama

# Monitor Ollama pod startup (downloads llama2 model)
kubectl logs -f -n deallus -l app.kubernetes.io/name=ollama
```

### 3.3 Verify Deployments

```bash
# Check all pods
kubectl get pods -n deallus

# Check ingress
kubectl get ingress -n deallus
# Should show ALB endpoint

# Test health endpoint
INGRESS_URL=$(kubectl get ingress -n deallus -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')
curl http://${INGRESS_URL}/api/health
```

## Step 4: Post-Deployment Verification

### 4.1 Database Connectivity

```bash
# Get connection string from Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id deallus-client1-connection \
  --query SecretString \
  --output text \
  --profile deallus-client1 | jq .

# Example output:
# {
#   "host": "deallus-client1.xxxxx.us-east-1.rds.amazonaws.com",
#   "port": 5432,
#   "database": "deallus",
#   "username": "deallus_admin",
#   "password": "xxxxxxxxxxxx"
# }
```

### 4.2 Redis Connectivity

```bash
# Get Redis endpoint
REDIS_ENDPOINT=$(tofu output -raw redis_endpoint)

# Test from pod
kubectl run -it redis-test --image=redis:7 --rm --restart=Never -- \
  redis-cli -h ${REDIS_ENDPOINT} -p 6379 PING
# Should return PONG
```

### 4.3 Check EFS Mounting

```bash
# Verify EFS is mounted in Ollama pod
kubectl exec -it -n deallus deployment/ollama -- df -h | grep /root/.ollama
# Should show EFS mount
```

## Troubleshooting

### Common Issues

**Route53 DNS not resolving:**
```bash
# Check delegation
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1A2B3C4D5E6F7 \
  --query 'ResourceRecordSets[?Name==`client1-xyzab-node.deallus.ai.`]'

# Should show NS records with client zone nameservers
```

**EKS nodes not ready:**
```bash
# Check node logs
kubectl describe nodes
kubectl logs -n kube-system -l k8s-app=aws-node
```

**Pod evictions:**
```bash
# Check node resources
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

## Next Steps

1. **Configure CI/CD** - Set up GitHub Actions for Helm deployments
2. **Setup Monitoring** - Configure CloudWatch dashboards
3. **Enable Backups** - Configure RDS automated backups
4. **Scale GPU** - Add more g4dn nodes as needed
5. **Add More Clients** - Repeat Step 2 for additional clients

---

**See also:** [troubleshooting.md](troubleshooting.md) for more issues and solutions.
