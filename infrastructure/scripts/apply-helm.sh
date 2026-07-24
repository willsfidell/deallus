#!/bin/bash
#
# apply-helm.sh - Deploy Helm charts for a client
#
# Usage: ./apply-helm.sh <client_id> <chart_name> [namespace]
#
# Examples:
# - ./apply-helm.sh client1 deallus-orchestrator
# - ./apply-helm.sh client1 ollama
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -lt 2 ]; then
    echo -e "${RED}Usage: $0 <client_id> <chart_name> [namespace]${NC}"
    echo ""
    echo "Available charts: deallus-orchestrator, ollama, infrastructure"
    exit 1
fi

CLIENT_ID=$1
CHART_NAME=$2
NAMESPACE=${3:-deallus}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHARTS_DIR="${SCRIPT_DIR}/../helm"
ENVS_DIR="${SCRIPT_DIR}/../environments"
CLIENT_ENV_DIR="${ENVS_DIR}/${CLIENT_ID}"
CHART_DIR="${CHARTS_DIR}/${CHART_NAME}"

if [ ! -d "$CHART_DIR" ]; then
    echo -e "${RED}Error: Chart not found at $CHART_DIR${NC}"
    exit 1
fi

if [ ! -d "$CLIENT_ENV_DIR" ]; then
    echo -e "${RED}Error: Client environment not found at $CLIENT_ENV_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Deploying chart: $CHART_NAME for client: $CLIENT_ID${NC}"

# Create namespace if it doesn't exist
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Deploy with Helm
helm upgrade --install "${CLIENT_ID}-${CHART_NAME}" "$CHART_DIR" \
    --namespace "$NAMESPACE" \
    --values "${CHART_DIR}/values.yaml"

# Apply client-specific values if they exist
if [ -f "${CHART_DIR}/values-${CLIENT_ID}.yaml" ]; then
    echo "Applying client-specific values..."
    helm upgrade "${CLIENT_ID}-${CHART_NAME}" "$CHART_DIR" \
        --namespace "$NAMESPACE" \
        --values "${CHART_DIR}/values.yaml" \
        --values "${CHART_DIR}/values-${CLIENT_ID}.yaml"
fi

echo -e "${GREEN}✓ Chart deployed successfully${NC}"
echo ""
echo "View deployment: kubectl get pods -n $NAMESPACE"
echo "View logs: kubectl logs -n $NAMESPACE -l app.kubernetes.io/instance=${CLIENT_ID}-${CHART_NAME}"
