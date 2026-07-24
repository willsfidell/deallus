#!/bin/bash
#
# create-client.sh - Provision a new Deallus client
#
# Usage: ./create-client.sh <client_id> <aws_account_id> <aws_region>
#
# This script:
# - Creates a new client environment directory
# - Generates a random subdomain suffix
# - Creates terraform.tfvars with client-specific values
# - Initializes S3 state bucket and DynamoDB lock table
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validate arguments
if [ $# -ne 3 ]; then
    echo -e "${RED}Usage: $0 <client_id> <aws_account_id> <aws_region>${NC}"
    echo ""
    echo "Example: $0 client2 987654321098 us-east-1"
    exit 1
fi

CLIENT_ID=$1
AWS_ACCOUNT_ID=$2
AWS_REGION=$3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENTS_DIR="${SCRIPT_DIR}/../environments"
CLIENT_ENV_DIR="${ENVIRONMENTS_DIR}/${CLIENT_ID}"

# Validate client ID format
if ! [[ "$CLIENT_ID" =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}Error: Client ID must contain only alphanumeric characters, hyphens, or underscores${NC}"
    exit 1
fi

# Check if client already exists
if [ -d "$CLIENT_ENV_DIR" ]; then
    echo -e "${RED}Error: Client environment already exists at $CLIENT_ENV_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Creating client environment for $CLIENT_ID...${NC}"

# Create client directory
mkdir -p "$CLIENT_ENV_DIR"

# Copy template files
echo "Copying template files..."
cp "${ENVIRONMENTS_DIR}/client-template/main.tf" "$CLIENT_ENV_DIR/main.tf"
cp "${ENVIRONMENTS_DIR}/client-template/variables.tf" "$CLIENT_ENV_DIR/variables.tf"
cp "${ENVIRONMENTS_DIR}/client-template/outputs.tf" "$CLIENT_ENV_DIR/outputs.tf"

# Create terraform.tfvars
echo "Creating terraform.tfvars..."
cat > "${CLIENT_ENV_DIR}/terraform.tfvars" << EOF
aws_region         = "$AWS_REGION"
client_id          = "$CLIENT_ID"
client_account_id  = "$AWS_ACCOUNT_ID"
root_zone_id       = "Z1234567890ABC"  # Replace with actual Route53 zone ID
root_zone_name     = "deallus.ai"

# Customize below as needed
orchestrator_desired_size = 2
gpu_desired_size          = 1
db_instance_class         = "db.t3.micro"
db_allocated_storage      = 20
redis_node_type           = "cache.t3.micro"
EOF

# Create backend.tf
echo "Creating backend.tf..."
cat > "${CLIENT_ENV_DIR}/backend.tf" << EOF
# $CLIENT_ID State Backend Configuration
terraform {
  backend "s3" {
    bucket         = "deallus-tfstate-${CLIENT_ID}-${AWS_ACCOUNT_ID}"
    key            = "terraform.tfstate"
    region         = "$AWS_REGION"
    encrypt        = true
    dynamodb_table = "deallus-tfstate-lock-${CLIENT_ID}"
  }
}
EOF

echo -e "${GREEN}✓ Client environment created at: $CLIENT_ENV_DIR${NC}"
echo ""
echo "Next steps:"
echo "1. Update terraform.tfvars with your Route53 zone ID"
echo "2. Run: cd $CLIENT_ENV_DIR && tofu init"
echo "3. Run: tofu plan && tofu apply"
echo ""
