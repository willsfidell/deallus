# Client Provisioning Guide

Step-by-step guide to add a new Deallus client to an existing deployment.

## Prerequisites

- Root account infrastructure already deployed (see [setup.md](setup.md))
- Route53 zone ID for `deallus.ai` (from root outputs)
- New AWS account for client (or use existing account with separate region)
- Credentials configured: `aws configure --profile deallus-client2`

## Quick Provision (5 minutes)

```bash
# 1. Create client environment
./scripts/create-client.sh client2 987654321098 us-east-1

# 2. Update configuration
cd environments/client2
vim terraform.tfvars  # Add Route53 zone ID

# 3. Deploy
tofu init
tofu apply

# 4. Deploy apps
cd ../..
./scripts/apply-helm.sh client2 deallus-orchestrator
./scripts/apply-helm.sh client2 ollama
```

## Detailed Walkthrough

### Phase 1: Preparation

#### 1.1 Gather Client Information

```bash
CLIENT_ID="client2"
AWS_ACCOUNT_ID="987654321098"
AWS_REGION="us-east-1"
ROOT_ZONE_ID="Z1A2B3C4D5E6F7"  # From root outputs
```

#### 1.2 Verify AWS Credentials

```bash
# Verify root account can access DNS
aws route53 list-hosted-zones --profile deallus-root
# Should list deallus.ai zone

# Verify client account
aws sts get-caller-identity --profile deallus-client2
# {
#   "Account": "987654321098",
#   "UserId": "AIDA...",
#   "Arn": "arn:aws:iam::987654321098:user/terraform"
# }
```

### Phase 2: Setup Client Environment

#### 2.1 Create Directory Structure

```bash
./scripts/create-client.sh client2 987654321098 us-east-1

# Output:
# Creating client environment for client2...
# Copying template files...
# Creating terraform.tfvars...
# Creating backend.tf...
# ✓ Client environment created at: environments/client2
```

#### 2.2 Review Generated Files

```bash
cd environments/client2

# Check contents
ls -la
# backend.tf         (with S3 bucket path)
# main.tf           (module references)
# variables.tf      (input variables)
# outputs.tf        (output values)
# terraform.tfvars  (client-specific config)
```

#### 2.3 Customize Configuration

```bash
vim terraform.tfvars
```

**Edit these values:**
```hcl
# From root outputs
root_zone_id = "Z1A2B3C4D5E6F7"

# Optional: Adjust sizing
orchestrator_desired_size = 2
orchestrator_max_size     = 4
gpu_desired_size          = 1
gpu_max_size              = 3

# Optional: Change instance types
orchestrator_instance_type = "t3.small"
gpu_instance_type          = "g4dn.xlarge"

# Database sizing
db_instance_class      = "db.t3.micro"
db_allocated_storage   = 20
```

### Phase 3: Prepare AWS Resources

#### 3.1 Create S3 Backend (First Time Only)

```bash
export AWS_PROFILE=deallus-client2

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"

# Create S3 bucket for state
aws s3 mb s3://deallus-tfstate-client2-${ACCOUNT_ID} --region ${REGION}

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket deallus-tfstate-client2-${ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket deallus-tfstate-client2-${ACCOUNT_ID} \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}
    }]
  }'

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name deallus-tfstate-lock-client2 \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST

# Wait for table creation
aws dynamodb wait table-exists --table-name deallus-tfstate-lock-client2
```

#### 3.2 Update Backend Configuration

```bash
# Back in environments/client2
ACCOUNT_ID=$(aws sts get-caller-identity --profile deallus-client2 --query Account --output text)

# Update backend.tf with account ID
sed -i "s/REPLACE_ACCOUNT_ID/${ACCOUNT_ID}/g" backend.tf

# Verify
cat backend.tf
# Should show: bucket = "deallus-tfstate-client2-987654321098"
```

### Phase 4: Infrastructure Deployment

#### 4.1 Initialize Terraform

```bash
export AWS_PROFILE=deallus-client2
tofu init

# Output:
# Initializing the backend...
# Initializing modules...
# Terraform has been successfully configured!
```

#### 4.2 Plan Deployment

```bash
tofu plan -out=tfplan

# Output summary:
# Plan: 87 to add, 0 to change, 0 to destroy
```

#### 4.3 Apply Deployment

```bash
tofu apply tfplan

# This will take 15-25 minutes. Creates:
# - VPC with 6 subnets
# - 3 NAT instances
# - EKS cluster with 3 node groups
# - RDS database
# - ElastiCache Redis
# - EFS storage
# - Route53 subdomain delegation
```

#### 4.4 Verify Deployment

```bash
# Save outputs
tofu output > client2-outputs.txt

# Verify resources created
aws eks describe-cluster --name deallus-client2 --profile deallus-client2
# Should show "ACTIVE" status

# Check subdomain
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1A2B3C4D5E6F7 \
  --profile deallus-root \
  --query 'ResourceRecordSets[?Name==`client2-*.node.deallus.ai.`]'
```

### Phase 5: Kubernetes Configuration

#### 5.1 Configure kubectl

```bash
# Get cluster name from outputs
CLUSTER_NAME=$(tofu output -raw eks_cluster_id)

# Update kubeconfig
aws eks update-kubeconfig \
  --name ${CLUSTER_NAME} \
  --region us-east-1 \
  --profile deallus-client2

# Verify access
kubectl get nodes

# Expected output:
# NAME                          STATUS   ROLES    AGE    VERSION
# ip-10-0-101-10.ec2.internal   Ready    <none>   5m     v1.28.1
# ip-10-0-102-20.ec2.internal   Ready    <none>   5m     v1.28.1
# ip-10-0-103-30.ec2.internal   Ready    <gpu>    3m     v1.28.1
```

#### 5.2 Create Application Namespace

```bash
kubectl create namespace deallus
kubectl label namespace deallus environment=client2
```

### Phase 6: Application Deployment

#### 6.1 Deploy Backend API

```bash
cd infrastructure

./scripts/apply-helm.sh client2 deallus-orchestrator

# Monitor deployment
kubectl get pods -n deallus -w

# Wait for migration job to complete
kubectl get jobs -n deallus
# Should see: deallus-orchestrator-migrate COMPLETED

# Check pod status (should be Running)
kubectl get pods -n deallus -l app.kubernetes.io/instance=client2-deallus-orchestrator
```

#### 6.2 Deploy Ollama GPU Workload

```bash
./scripts/apply-helm.sh client2 ollama

# Monitor model download
kubectl logs -f -n deallus deployment/ollama

# This will output:
# Downloading model: llama2
# pulling manifest
# pulling 6b... (layers)
# Once done: "success"
```

#### 6.3 Verify Deployments

```bash
# Check all pods
kubectl get pods -n deallus

# Expected output:
# NAME                                      READY   STATUS    RESTARTS
# deallus-orchestrator-xxxxx                1/1     Running   0
# deallus-orchestrator-xxxxx                1/1     Running   0
# ollama-xxxxx                              1/1     Running   0

# Check services
kubectl get svc -n deallus

# Check ingress
kubectl get ingress -n deallus
# Should show ALB endpoint with domain
```

### Phase 7: Testing

#### 7.1 Get Subdomain and Endpoint

```bash
# Get subdomain from DNS module output
SUBDOMAIN=$(tofu output -raw subdomain)

# Get ALB endpoint
INGRESS_URL=$(kubectl get ingress -n deallus -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}')

echo "Subdomain: ${SUBDOMAIN}"
echo "ALB Endpoint: ${INGRESS_URL}"
```

#### 7.2 Test Health Endpoint

```bash
# Test via ALB (before DNS propagates)
curl -k http://${INGRESS_URL}/api/health

# Expected response:
# {"status": "healthy", "timestamp": "2025-01-28T..."}
```

#### 7.3 Test Database Connectivity

```bash
# Get connection string
aws secretsmanager get-secret-value \
  --secret-id deallus-client2-connection \
  --query SecretString \
  --output text \
  --profile deallus-client2 | jq .

# Connect from pod
kubectl run -it db-test \
  --image=postgres:16 \
  --rm --restart=Never \
  -- psql -h deallus-client2.xxxxx.us-east-1.rds.amazonaws.com \
  -U deallus_admin -d deallus -c "SELECT version();"
```

#### 7.4 Test Redis Connectivity

```bash
# Get endpoint
REDIS_ENDPOINT=$(tofu output -raw redis_endpoint)

# Test from pod
kubectl run -it redis-test \
  --image=redis:7 \
  --rm --restart=Never \
  -- redis-cli -h ${REDIS_ENDPOINT} PING

# Expected: PONG
```

### Phase 8: Post-Deployment

#### 8.1 Configure Logging

```bash
# Enable pod logs streaming to CloudWatch (optional)
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: deallus
data:
  fluent-bit.conf: |
    [INPUT]
        Name              tail
        Path              /var/log/containers/*.log
        multiline.parser  docker, cri
    [OUTPUT]
        Name              cloudwatch_logs
        Match             *
        region            us-east-1
        log_group_name    /aws/eks/deallus-client2
        log_stream_prefix deallus-
EOF
```

#### 8.2 Setup Backups

```bash
# Enable automated backups (already configured in Terraform)
# Verify backup window
aws rds describe-db-instances \
  --db-instance-identifier deallus-client2 \
  --query 'DBInstances[0].PreferredBackupWindow' \
  --profile deallus-client2
```

#### 8.3 Create DNS CNAME (Optional)

```bash
# If using custom domain (e.g., api.myclient.com)
aws route53 change-resource-record-sets \
  --hosted-zone-id <MYCLIENT_ZONE_ID> \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.myclient.com",
        "Type": "CNAME",
        "TTL": 300,
        "ResourceRecords": [{"Value": "'${SUBDOMAIN}'"}]
      }
    }]
  }'
```

## Troubleshooting

### Infrastructure Issues

**Nodes not ready:**
```bash
kubectl describe nodes
# Check conditions: Ready, MemoryPressure, DiskPressure, etc.

# Check system pods
kubectl get pods -n kube-system
# All should be Running
```

**Database can't connect:**
```bash
# Check security group
aws ec2 describe-security-groups \
  --group-ids sg-xxxxx \
  --profile deallus-client2

# Verify RDS is in same VPC
aws rds describe-db-instances \
  --db-instance-identifier deallus-client2 \
  --query 'DBInstances[0].DBSubnetGroup' \
  --profile deallus-client2
```

**DNS not resolving:**
```bash
# Check NS records delegation
aws route53 list-resource-record-sets \
  --hosted-zone-id Z1A2B3C4D5E6F7 \
  --profile deallus-root | grep client2

# Should show NS records
```

### Kubernetes Issues

**Pod not starting:**
```bash
kubectl describe pod <POD_NAME> -n deallus
# Check Events section for error details

kubectl logs <POD_NAME> -n deallus
# Check application logs
```

**Ingress not working:**
```bash
# Check ingress status
kubectl describe ingress -n deallus

# Verify ALB controller is running
kubectl get pods -n kube-system | grep alb

# Check ingress controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

## Cleanup (If Needed)

### Remove Single Client

```bash
# Destroy infrastructure
./scripts/destroy-client.sh client2

# Delete local directory
rm -rf environments/client2
```

### Full Account Cleanup

```bash
# Run destroy script (removes all resources)
./scripts/destroy-client.sh client2

# Delete S3 bucket (and state)
ACCOUNT_ID=$(aws sts get-caller-identity --profile deallus-client2 --query Account --output text)
aws s3 rb s3://deallus-tfstate-client2-${ACCOUNT_ID} \
  --force --profile deallus-client2

# Delete DynamoDB table
aws dynamodb delete-table \
  --table-name deallus-tfstate-lock-client2 \
  --profile deallus-client2
```

---

**Next:** See [troubleshooting.md](troubleshooting.md) for common issues and solutions.
