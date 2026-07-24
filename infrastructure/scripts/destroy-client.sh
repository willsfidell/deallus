#!/bin/bash
#
# destroy-client.sh - Teardown a Deallus client
#
# Usage: ./destroy-client.sh <client_id>
#
# This script safely tears down client infrastructure:
# - Deletes Helm releases
# - Runs tofu destroy
# - Optionally deletes state bucket
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -ne 1 ]; then
    echo -e "${RED}Usage: $0 <client_id>${NC}"
    exit 1
fi

CLIENT_ID=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_ENV_DIR="${SCRIPT_DIR}/../environments/${CLIENT_ID}"

if [ ! -d "$CLIENT_ENV_DIR" ]; then
    echo -e "${RED}Error: Client environment not found at $CLIENT_ENV_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will destroy all infrastructure for client: $CLIENT_ID${NC}"
read -p "Are you sure? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# Configure kubectl
echo "Configuring kubectl..."
CLUSTER_NAME=$(grep 'cluster_name.*=' "$CLIENT_ENV_DIR/main.tf" | grep -oP '(?<=")[^"]*(?=")' | head -1)
AWS_REGION=$(grep 'aws_region.*=' "$CLIENT_ENV_DIR/terraform.tfvars" | grep -oP '(?==\s*")[^"]*(?=")' | head -1)

aws eks update-kubeconfig --name "deallus-${CLIENT_ID}" --region "${AWS_REGION:-us-east-1}" 2>/dev/null || true

# Delete Helm releases
echo -e "${YELLOW}Deleting Helm releases...${NC}"
helm list -n deallus | awk 'NR>1 {print $1}' | xargs -I {} helm uninstall {} -n deallus 2>/dev/null || true

# Run tofu destroy
echo -e "${YELLOW}Running tofu destroy...${NC}"
cd "$CLIENT_ENV_DIR"
tofu destroy

echo -e "${GREEN}✓ Client $CLIENT_ID has been destroyed${NC}"
