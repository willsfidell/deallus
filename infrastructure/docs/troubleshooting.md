# Troubleshooting Guide

Common issues and solutions for Deallus infrastructure deployment and operation.

## Terraform / OpenTofu Issues

### "Error acquiring the lock"

**Symptom:** Multiple people applying Terraform simultaneously

```
Error: Error acquiring the lock: ConditionalCheckFailedException:
The conditional request failed
```

**Solution:**
```bash
# Terraform is holding a lock (usually from a failed operation)
# Force unlock (use with caution):
tofu force-unlock <LOCK_ID>

# Better: check what's happening
aws dynamodb scan --table-name deallus-tfstate-lock-client1 \
  --query 'Items[0].LockID'
```

### State File Corruption

**Symptom:** Terraform can't parse state file

```
Error: Error reading state for aws_eks_cluster.main
```

**Solution:**
```bash
# 1. Create backup
aws s3 cp s3://deallus-tfstate-client1-xxx/terraform.tfstate \
  terraform.tfstate.backup

# 2. Restore previous version
aws s3api get-object \
  --bucket deallus-tfstate-client1-xxx \
  --key terraform.tfstate \
  --version-id <OLD_VERSION_ID> \
  terraform.tfstate

# 3. Re-apply
tofu plan && tofu apply
```

### Module Not Found

**Symptom:**
```
Error: Error downloading modules: Error loading modules:
module not found
```

**Solution:**
```bash
# Make sure you're in correct directory
pwd  # Should be environments/client1

# Reinitialize modules
tofu get -update
tofu init -upgrade
```

---

## AWS Infrastructure Issues

### NAT Instance Not Working (Internet Disconnected)

**Symptom:** Pods can't reach external services

**Diagnosis:**
```bash
# 1. Check NAT instance is running
aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=*nat*" \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name}'

# 2. Check route tables
aws ec2 describe-route-tables \
  --filters "Name=vpc-id,Values=vpc-xxxxx" \
  --query 'RouteTables[].[RouteTableId,Routes[].DestinationCidrBlock]'

# 3. Check security group
aws ec2 describe-security-groups \
  --group-ids sg-nat-xxxxx \
  --query 'SecurityGroups[].IpPermissions'
```

**Solutions:**

**Issue: NAT instance stopped**
```bash
# Restart it
aws ec2 start-instances --instance-ids i-xxxxx

# Re-enable source/dest check (if it was disabled)
aws ec2 modify-instance-attribute --instance-id i-xxxxx \
  --no-source-dest-check
```

**Issue: Wrong route table**
```bash
# Update private route table
aws ec2 create-route \
  --route-table-id rtb-xxxxx \
  --destination-cidr-block 0.0.0.0/0 \
  --instance-id i-nat-xxxxx
```

### RDS Database Connection Failed

**Symptom:** Pods can't reach RDS

```
psql: error: could not translate host name "deallus-client1..." to address
```

**Diagnosis:**
```bash
# 1. Check RDS is running
aws rds describe-db-instances \
  --db-instance-identifier deallus-client1 \
  --query 'DBInstances[0].DBInstanceStatus'

# 2. Check security group allows 5432 from EKS
aws ec2 describe-security-groups \
  --group-ids sg-rds-xxxxx \
  --query 'SecurityGroups[0].IpPermissions'

# 3. Test from EKS node
kubectl run -it debug --image=postgres:16 --rm -- \
  psql -h deallus-client1.xxxxx.us-east-1.rds.amazonaws.com \
  -U deallus_admin -d deallus -c "SELECT 1"
```

**Solutions:**

**Issue: Security group missing port 5432**
```bash
# Add ingress rule
aws ec2 authorize-security-group-ingress \
  --group-id sg-rds-xxxxx \
  --protocol tcp --port 5432 \
  --source-group sg-eks-nodes-xxxxx
```

**Issue: RDS in wrong subnet**
```bash
# RDS must be in VPC's private subnets
# Verify DB subnet group
aws rds describe-db-subnet-groups \
  --query 'DBSubnetGroups[0].Subnets'
```

### Redis Connection Timeout

**Symptom:** Redis connection refused on port 6379

**Diagnosis:**
```bash
# 1. Check Redis cluster status
aws elasticache describe-cache-clusters \
  --cache-cluster-id deallus-client1 \
  --show-cache-node-info \
  --query 'CacheClusters[0].CacheNodeType'

# 2. Check security group
aws ec2 describe-security-groups \
  --group-ids sg-redis-xxxxx \
  --query 'SecurityGroups[0].IpPermissions'

# 3. Test from pod
kubectl run -it redis-test --image=redis:7 --rm -- \
  redis-cli -h <REDIS_ENDPOINT> -p 6379 PING
```

**Solutions:**

**Issue: Security group missing port 6379**
```bash
aws ec2 authorize-security-group-ingress \
  --group-id sg-redis-xxxxx \
  --protocol tcp --port 6379 \
  --source-group sg-eks-nodes-xxxxx
```

---

## EKS Cluster Issues

### Nodes Not Ready

**Symptom:**
```
kubectl get nodes
# Shows: NotReady, MemoryPressure, DiskPressure
```

**Diagnosis:**
```bash
# Check node conditions
kubectl describe node <NODE_NAME>

# Check node logs
kubectl logs -n kube-system -l component=kubelet

# Check system pods
kubectl get pods -n kube-system
```

**Solutions:**

**Issue: Insufficient capacity**
```bash
# Increase node group size
tofu apply -var orchestrator_max_size=6

# Or manually scale
aws autoscaling update-auto-scaling-group \
  --auto-scaling-group-name deallus-client1-orchestrator-asg \
  --desired-capacity 3
```

**Issue: CNI not working**
```bash
# Check AWS VPC CNI
kubectl get pods -n kube-system -l k8s-app=aws-node

# Restart CNI
kubectl rollout restart daemonset -n kube-system aws-node
```

### Pods Pending

**Symptom:**
```
kubectl get pods -n deallus
# Shows: Pending
```

**Diagnosis:**
```bash
# Check pod events
kubectl describe pod <POD_NAME> -n deallus
# Look for "insufficient cpu/memory" or taint tolerance issues

# Check node resources
kubectl top nodes
kubectl top pods -n deallus
```

**Solutions:**

**Issue: Taint not tolerated (GPU pod on CPU node)**
```bash
# GPU pods must tolerate nvidia.com/gpu taint
# Check pod tolerations
kubectl get pod <POD_NAME> -n deallus -o yaml | grep -A 5 tolerations

# Fix: Update Helm values
# helm/ollama/values.yaml:
# tolerations:
#   - key: nvidia.com/gpu
#     operator: Equal
#     value: "true"
#     effect: NoSchedule
```

**Issue: Insufficient resources**
```bash
# Add more nodes
tofu apply -var gpu_desired_size=2

# Or check what's using resources
kubectl describe nodes
# Look for "Allocated resources" section
```

### Pod Crash Loop

**Symptom:**
```
kubectl get pods -n deallus
# Shows: CrashLoopBackOff
```

**Diagnosis:**
```bash
# Check pod logs
kubectl logs <POD_NAME> -n deallus --previous

# Check pod events
kubectl describe pod <POD_NAME> -n deallus
```

**Solutions:**

**Issue: Environment variable not set**
```bash
# Check pod environment
kubectl exec <POD_NAME> -n deallus -- env | grep DATABASE

# Update Helm values if missing
helm get values client1-deallus-orchestrator -n deallus
```

**Issue: Database not ready**
```bash
# Check database is running
aws rds describe-db-instances \
  --db-instance-identifier deallus-client1 \
  --query 'DBInstances[0].DBInstanceStatus'

# If "creating", wait for completion
```

### Pod Eviction

**Symptom:**
```
kubectl get pods -n deallus
# Pod was evicted due to: Reason: DiskPressure
```

**Diagnosis:**
```bash
# Check node disk usage
kubectl debug node/<NODE_NAME> -it --image=ubuntu

# Or via AWS Systems Manager
aws ssm start-session --target i-node-xxxxx
df -h
```

**Solutions:**

**Clean up old images:**
```bash
# On each node (via Systems Manager or SSH)
docker image prune -a

# Or resize volume
aws ec2 modify-volume --volume-id vol-xxxxx --size 100
```

---

## Kubernetes/Helm Issues

### Ingress Not Working

**Symptom:** ALB endpoint shows 503 error

**Diagnosis:**
```bash
# 1. Check ingress resource
kubectl get ingress -n deallus
kubectl describe ingress -n deallus

# 2. Check ALB exists
aws elbv2 describe-load-balancers

# 3. Check target groups
aws elbv2 describe-target-groups --query 'TargetGroups[]'

# 4. Check targets are healthy
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
```

**Solutions:**

**Issue: ALB controller not running**
```bash
kubectl get pods -n kube-system | grep alb

# If not there, install it
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set serviceAccount.create=true
```

**Issue: Targets not healthy**
```bash
# Check security groups allow inbound on 8000
aws ec2 describe-security-groups --group-ids sg-eks-nodes-xxxxx

# Add rule if missing
aws ec2 authorize-security-group-ingress \
  --group-id sg-eks-nodes-xxxxx \
  --protocol tcp --port 8000 \
  --source-group sg-alb-xxxxx
```

### Certificate Not Issued

**Symptom:** HTTPS fails, certificate not found

**Diagnosis:**
```bash
# Check cert-manager
kubectl get pods -n cert-manager

# Check certificate resource
kubectl get certificate -n deallus

# Check cert details
kubectl describe certificate -n deallus <CERT_NAME>

# Check challenge
kubectl get challenges -n deallus
kubectl describe challenge -n deallus <CHALLENGE_NAME>
```

**Solutions:**

**Issue: cert-manager not installed**
```bash
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  -n cert-manager --create-namespace \
  --set installCRDs=true
```

**Issue: ClusterIssuer not created**
```bash
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@deallus.ai
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: alb
EOF
```

---

## Application Issues

### Database Migrations Failed

**Symptom:** Application pod crashes on startup

```
ERROR: alembic.error.CommandError: Can't locate revision identified by ''
```

**Solution:**
```bash
# 1. Check migration job
kubectl get jobs -n deallus
kubectl logs -n deallus job/deallus-orchestrator-migrate

# 2. If failed, run manually
./scripts/emergency-migrate.sh client1

# 3. Check database state
kubectl exec -it <POD> -n deallus -- \
  psql -h $DATABASE_HOST -U $DATABASE_USERNAME -d $DATABASE_NAME \
  -c "SELECT * FROM alembic_version;"
```

### API Health Check Failing

**Symptom:** Liveness probe failing, pod restarting

**Diagnosis:**
```bash
# Check API logs
kubectl logs -f <POD> -n deallus

# Test health endpoint locally
kubectl exec -it <POD> -n deallus -- \
  curl -s http://localhost:8000/api/health | jq .

# Check database connectivity
kubectl exec -it <POD> -n deallus -- \
  python -c "import psycopg2; conn = psycopg2.connect(...); print('OK')"
```

**Solutions:**

**Issue: Database unreachable**
```bash
# Update DATABASE_HOST in deployment
helm get values client1-deallus-orchestrator -n deallus | grep DATABASE

# Update if needed
helm upgrade client1-deallus-orchestrator \
  helm/deallus-orchestrator -n deallus \
  -f helm/deallus-orchestrator/values.yaml \
  --set database.host=<NEW_HOST>
```

### Ollama Model Not Loading

**Symptom:** Ollama pod running but model command fails

**Diagnosis:**
```bash
# Check init container logs
kubectl logs <POD> -n deallus -c download-models

# Check EFS mount
kubectl exec -it <POD> -n deallus -- \
  df -h | grep ollama

# Check model directory
kubectl exec -it <POD> -n deallus -- \
  ls -lah /root/.ollama/models/
```

**Solutions:**

**Issue: EFS not mounted**
```bash
# Check PVC
kubectl get pvc -n deallus
kubectl describe pvc -n deallus ollama-pvc

# Check mount target exists
aws efs describe-mount-targets \
  --file-system-id fs-xxxxx
```

**Issue: Model download failed**
```bash
# Increase timeout in Helm values
helm upgrade client1-ollama \
  helm/ollama -n deallus \
  --set models.downloadTimeout="1200"

# Manual download
kubectl exec -it <POD> -n deallus -- \
  ollama pull llama2
```

---

## Debugging Commands Cheatsheet

```bash
# Get all resource status
kubectl get all -n deallus

# Debug a failing pod
kubectl debug pod/<POD> -it -n deallus --image=busybox

# Port forward for testing
kubectl port-forward -n deallus svc/deallus-orchestrator 8000:8000

# Stream logs from all pods
kubectl logs -f -n deallus --all-containers=true -l app=deallus

# SSH into node
kubectl debug node/<NODE> -it --image=ubuntu

# Get node metrics
kubectl top nodes
kubectl top pods -n deallus

# Describe all events
kubectl get events -n deallus --sort-by='.lastTimestamp'

# Check resource limits
kubectl describe resourcequota -n deallus

# Verify RBAC
kubectl auth can-i get secrets -n deallus --as=system:serviceaccount:deallus:deallus-orchestrator
```

---

## Performance Optimization

### Slow Database Queries

```bash
# Enable PostgreSQL slow query log
aws rds modify-db-parameter-group \
  --db-parameter-group-name default.postgres16 \
  --parameters ParameterName=log_min_duration_statement,ParameterValue=1000,ApplyMethod=immediate

# Query CloudWatch logs
aws logs filter-log-events \
  --log-group-name /aws/rds/instance/deallus-client1/postgresql \
  --filter-pattern 'duration'
```

### High CPU Usage

```bash
# Check which pods using CPU
kubectl top pods -n deallus

# Check node CPU
kubectl top nodes

# Scale up if needed
tofu apply -var orchestrator_max_size=6
```

### Memory Leaks

```bash
# Monitor memory over time
kubectl top pods -n deallus --containers

# If growing: restart pod
kubectl rollout restart deployment/deallus-orchestrator -n deallus

# Check for memory limits
kubectl get pods -n deallus -o jsonpath='{.items[].spec.containers[].resources.limits.memory}'
```

---

**Need more help?** Check the [architecture.md](architecture.md) for design details or run `tofu show` to inspect current state.
