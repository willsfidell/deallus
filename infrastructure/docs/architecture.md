# Architecture Documentation

Comprehensive reference for the Deallus infrastructure architecture, design decisions, and components.

## Overview

Deallus uses a **multi-tenant, multi-account AWS architecture** with complete tenant isolation while sharing infrastructure components (DNS, state management).

### Tenets

1. **Complete Isolation**: Each client in separate AWS account
2. **Cost Optimization**: Spot instances, right-sized resources, autoscaling
3. **Kubernetes-Native**: All workloads run on EKS with Helm
4. **Infrastructure as Code**: 100% reproducible deployments
5. **Automated Scaling**: Horizontal and vertical scaling built-in

---

## Account Architecture

```
┌─────────────────────────────────────────────────────┐
│           AWS Organization (Root)                   │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Root Account (xxx-root)                      │  │
│  │                                              │  │
│  │  Route53 Hosted Zone: deallus.ai            │  │
│  │  ├─ NS: client1-xyzab-node.deallus.ai      │  │
│  │  ├─ NS: client2-abcde-node.deallus.ai      │  │
│  │  └─ NS: client3-pqrst-node.deallus.ai      │  │
│  │                                              │  │
│  │  S3 Buckets:                                 │  │
│  │  ├─ deallus-tfstate-root-xxx                │  │
│  │  ├─ deallus-tfstate-client1-xxx             │  │
│  │  ├─ deallus-tfstate-client2-xxx             │  │
│  │  └─ deallus-tfstate-client3-xxx             │  │
│  │                                              │  │
│  │  DynamoDB Lock Tables:                       │  │
│  │  ├─ deallus-tfstate-lock-root               │  │
│  │  ├─ deallus-tfstate-lock-client1            │  │
│  │  ├─ deallus-tfstate-lock-client2            │  │
│  │  └─ deallus-tfstate-lock-client3            │  │
│  └──────────────────────────────────────────────┘  │
└────┬─────────────────────────┬─────────────────────┘
     │                         │
     │                         │
   ┌─▼──────────────┐      ┌──▼──────────────┐
   │  Client        │      │  Client         │
   │  Account 1     │      │  Account 2      │
   │  (123456789..  │      │  (987654321..   │
   │  )             │      │  )              │
   └────────────────┘      └─────────────────┘
```

### Benefits

- **Blast Radius**: Each client failure isolated to single account
- **Compliance**: Separate billing, audit logs, IAM policies per client
- **Scalability**: Can easily onboard new customers
- **Cost Allocation**: Transparent per-customer costs

---

## Networking Architecture

### VPC Design

```
VPC: 10.0.0.0/16
│
├── Public Subnets (NAT Exit, ALB)
│   ├── 10.0.1.0/24 (us-east-1a) → NAT Instance 1 → EIP
│   ├── 10.0.2.0/24 (us-east-1b) → NAT Instance 2 → EIP
│   └── 10.0.3.0/24 (us-east-1c) → NAT Instance 3 → EIP
│
├── Private Subnets (EKS, RDS, Redis, EFS)
│   ├── 10.0.101.0/24 (us-east-1a)
│   ├── 10.0.102.0/24 (us-east-1b)
│   └── 10.0.103.0/24 (us-east-1c)
│
├── Internet Gateway → Route53 (inbound)
│
└── NAT Instances → Internet (outbound from private)
```

### Subnet Strategy

| Subnet | CIDR | Use | Instances | Route |
|--------|------|-----|-----------|-------|
| public-1 | 10.0.1.0/24 | ALB, NAT | t4g.nano | IGW |
| public-2 | 10.0.2.0/24 | ALB, NAT | t4g.nano | IGW |
| public-3 | 10.0.3.0/24 | ALB, NAT | t4g.nano | IGW |
| private-1 | 10.0.101.0/24 | EKS, RDS, etc | EKS nodes | NAT-1 |
| private-2 | 10.0.102.0/24 | EKS, RDS, etc | EKS nodes | NAT-2 |
| private-3 | 10.0.103.0/24 | EKS, RDS, etc | EKS nodes | NAT-3 |

### Why NAT Instances?

We use **NAT Instances** (t4g.nano) instead of NAT Gateways for cost optimization:
- **NAT Instance**: ~$3/month (t4g.nano) + data transfer
- **NAT Gateway**: $32/month per gateway + data transfer

For POC, NAT instances provide sufficient throughput (500 Mbps) at 1/10th the cost.

### Security Groups

```
┌─────────────────────────────────────────┐
│         Internet (0.0.0.0/0)            │
└────────────┬────────────────────────────┘
             │ :443 HTTPS
             ▼
         ┌────────┐
         │  ALB   │
         └───┬────┘
             │ :8000 HTTP (internal)
    ┌────────┴─────────┐
    │   EKS Cluster    │
    │                  │
    ├──────┬───────────┤
    │      │ :5432     │ :6379     │ :2049
    ▼      ▼           ▼           ▼
  Pods → RDS       Redis        EFS
```

---

## EKS Cluster Design

### Node Groups

#### 1. Orchestrator Node Group
```yaml
Name: deallus-client1-orchestrator
Instance Type: t3.small
Capacity: ON_DEMAND (cost-stable)
Desired: 2
Min: 2
Max: 4
Labels:
  workload: orchestrator
```

**Runs:**
- Deallus API (FastAPI)
- Kube system addons
- Ingress controllers

#### 2. GPU Node Group
```yaml
Name: deallus-client1-gpu
Instance Type: g4dn.xlarge (1x T4 GPU)
Capacity: SPOT (70% savings)
Desired: 1
Min: 1
Max: 3
Labels:
  workload: gpu
  gpu: "true"
Taints:
  - Key: nvidia.com/gpu
    Value: "true"
    Effect: NoSchedule
```

**Runs:**
- Ollama inference server
- GPU-accelerated workloads

### Addons

```
aws-vpc-cni              → Pod networking (IP per pod)
coredns                  → DNS (kube-dns)
kube-proxy               → Service routing
aws-ebs-csi-driver       → EBS volumes (for future use)
aws-efs-csi-driver       → EFS mounting (Ollama models)
```

### IRSA (IAM Roles for Service Accounts)

Pods authenticate to AWS using OpenID Connect:

```
Pod (deallus-orchestrator)
  ↓
ServiceAccount (kube-system)
  ↓
OIDC Provider (eks.amazonaws.com)
  ↓
IAM Role (deallus-client1-pod-role)
  ↓
AWS Service (Secrets Manager, CloudWatch)
```

**Benefits:**
- No static credentials in pods
- Fine-grained per-service IAM policies
- Automatic credential rotation

---

## Data Layer

### RDS PostgreSQL

```yaml
Engine: PostgreSQL 16
Instance Class: db.t3.micro
Storage: 20GB GP3
Multi-AZ: false (POC only)
Backup Retention: 7 days
Encryption: AES256
```

**Credentials:**
- Stored in AWS Secrets Manager
- Injected into pods via environment variables
- Rotated manually (can be automated)

### ElastiCache Redis

```yaml
Engine: Redis 7.0
Node Type: cache.t3.micro
Num Nodes: 1
Encryption: At-rest only (transit disabled for speed)
Logs: CloudWatch
```

**Used for:**
- Session caching (1 hour TTL)
- Conversation context (temporary)
- Model state between requests

### EFS Storage

```yaml
Filesystem: EFS Standard (bursting mode)
Backup: Enabled
Encryption: AES256
AccessPoint: /ollama-models (fixed mount)
Quota: 100GB
```

**Why EFS?**
- Shared across all Ollama pods
- Survives pod restarts
- Models persist between deployments
- 100GB easily holds 3-5 Llama2 models

---

## DNS Architecture

### Subdomain Delegation

```
Root Zone (Route53)
deallus.ai (Z1A2B3C4D5E6F7)
│
├─ NS: ns-1234.awsdns-1.com
├─ NS: ns-5678.awsdns-2.co.uk
└─ NS Records for clients:
   │
   ├─ client1-xyzab-node.deallus.ai NS [random-1.awsdns-x.com, ...]
   ├─ client2-abcde-node.deallus.ai NS [random-2.awsdns-y.com, ...]
   └─ client3-pqrst-node.deallus.ai NS [random-3.awsdns-z.com, ...]
```

**Random Suffix Strategy:**
- Prevents subdomain collisions
- Format: `{client_id}-{random_5_chars}-node.deallus.ai`
- Example: `client1-xyzab-node.deallus.ai`

### TLS Certificates

Using **cert-manager** with Let's Encrypt:

```yaml
ClusterIssuer: letsencrypt-prod
Certificate:
  - Domain: *.client1-xyzab-node.deallus.ai
    Issuer: Let's Encrypt
    Auto-renewal: 30 days before expiry
```

---

## Helm Chart Architecture

### Chart 1: deallus-orchestrator

```
deallus-orchestrator
├── Deployment (2 replicas)
│   └── FastAPI container
├── Service (ClusterIP)
├── Ingress (ALB)
├── HPA (autoscale 2-4 replicas)
├── ServiceAccount (IRSA)
├── ConfigMap (non-secret config)
└── Job (pre-install: Alembic migrations)
```

### Chart 2: ollama

```
ollama
├── Deployment (1 replica initially)
├── Service (ClusterIP, internal only)
├── PVC (EFS mount)
├── HPA (autoscale 1-3 replicas)
├── InitContainer (download llama2)
└── ServiceAccount
```

### Values Hierarchy

```
values.yaml (defaults)
    ↓
values-client1.yaml (client-specific overrides)
    ↓
Final effective values
```

---

## Provisioning Flow

### Step 1: Root Account (One-time)

```
create-root-env
    ↓
    ├─ Create Route53 zone (deallus.ai)
    ├─ Create S3 buckets (state per client)
    ├─ Create DynamoDB tables (locks)
    ├─ Output: hosted_zone_id, name_servers
    └─ Manual: Update domain registrar with NS records
```

### Step 2: Client Account

```
create-client.sh
    ↓
    ├─ Create client directory from template
    ├─ Generate random subdomain suffix
    ├─ Create terraform.tfvars
    └─ Create backend.tf with S3 path

tofu apply (client environment)
    ↓
    ├─ Networking module
    │   ├─ VPC, subnets, NAT instances
    │   └─ Security groups
    ├─ EKS module
    │   ├─ Cluster + node groups
    │   ├─ OIDC provider
    │   └─ Addons
    ├─ Database module
    │   ├─ RDS instance
    │   └─ Secrets Manager
    ├─ Cache module
    │   └─ ElastiCache Redis
    ├─ Storage module
    │   ├─ EFS filesystem
    │   ├─ Mount targets (3 AZs)
    │   └─ Access point
    └─ DNS module
        ├─ Client hosted zone
        ├─ NS records (delegation)
        └─ A record placeholder

apply-helm.sh
    ↓
    ├─ Deploy deallus-orchestrator
    │   └─ Migration job runs
    ├─ Deploy ollama
    │   └─ Downloads llama2 model
    └─ Deploy infrastructure charts
        ├─ AWS Load Balancer Controller
        ├─ cert-manager
        └─ cluster-autoscaler
```

---

## Scaling Considerations

### Vertical Scaling

| Component | Current | Recommended | Cost Impact |
|-----------|---------|-------------|------------|
| Orchestrator nodes | t3.small | t3.medium | +$8/month each |
| GPU nodes | g4dn.xlarge | g4dn.2xlarge | +$200/month |
| RDS | db.t3.micro | db.t3.small | +$11/month |
| Redis | cache.t3.micro | cache.t3.small | +$9/month |
| EFS | 100GB | 200GB | +$18/month |

### Horizontal Scaling

```bash
# Scale orchestrator to 4 nodes
tofu apply -var orchestrator_max_size=6

# Add 2 more GPU nodes
tofu apply -var gpu_max_size=5 -var gpu_desired_size=2

# EKS autoscaler will automatically add nodes based on:
# - Resource requests (CPU, memory)
# - Pod scheduling requirements
```

### Autoscaling

- **HPA (Horizontal Pod Autoscaler)**: Scales pod replicas based on CPU
- **Cluster Autoscaler**: Adds EC2 nodes when pods can't fit
- **Spot Instance Interruption Handlers**: Gracefully drain GPU nodes on spot termination

---

## Disaster Recovery

### Backup Strategy

```yaml
RDS:
  - Automated backups: 7 days
  - Snapshots: Manual before major updates
  - Recovery: 30 seconds to restore to point-in-time

EFS:
  - Backup policy: Enabled
  - Recovery: EFS access points frozen after deletion for 30 days

S3 State:
  - Versioning: Enabled
  - MFA Delete: Can be enabled for production
  - Cross-Region Replication: Can be configured
```

### Recovery Procedures

**Database corruption:**
```bash
# Restore from latest snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier deallus-client1-restored \
  --db-snapshot-identifier deallus-client1-snapshot-xxx
```

**State file corruption:**
```bash
# Restore from S3 versioning
aws s3api get-object \
  --bucket deallus-tfstate-client1-xxx \
  --key terraform.tfstate \
  --version-id xxxxx \
  terraform.tfstate.restored
```

---

## Security Hardening (Future)

- [ ] Enable VPC Flow Logs
- [ ] Configure GuardDuty for threat detection
- [ ] Enable AWS Config for compliance checks
- [ ] Setup CloudTrail for audit logging
- [ ] Enable RDS encryption with KMS (customer-managed keys)
- [ ] Setup WAF rules on ALB
- [ ] Enable Pod Security Policy in EKS
- [ ] Configure Network Policies for east-west traffic control

---

## Cost Optimization

### Current Optimizations

✅ NAT instances instead of NAT Gateway (-$29/month)
✅ Spot instances for GPU nodes (-70%)
✅ Single RDS instance (no Multi-AZ)
✅ t4g.nano for NAT (better price/perf than t3)
✅ Auto-shutdown of non-essential resources

### Future Optimizations

- [ ] Reserved instances for orchestrator nodes (50% savings)
- [ ] Savings plans for EKS control plane
- [ ] Multi-AZ RDS for HA (costs ~+$15-20/month)
- [ ] EBS volumes instead of EFS for static models (50% cheaper)
- [ ] Lambda for irregular workloads (billing only for execution)

---

## References

- [AWS EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Helm Chart Documentation](https://helm.sh/docs/)
