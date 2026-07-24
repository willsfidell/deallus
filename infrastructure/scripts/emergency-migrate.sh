#!/bin/bash
#
# emergency-migrate.sh - Run database migrations manually
#
# Usage: ./emergency-migrate.sh <client_id> [namespace]
#
# Use this when the init job fails to properly migrate the database.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ $# -lt 1 ]; then
    echo -e "${RED}Usage: $0 <client_id> [namespace]${NC}"
    exit 1
fi

CLIENT_ID=$1
NAMESPACE=${2:-deallus}

echo -e "${YELLOW}Running emergency database migration for client: $CLIENT_ID${NC}"

# Find the orchestrator pod
POD=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/instance=${CLIENT_ID}-deallus-orchestrator" \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

if [ -z "$POD" ]; then
    echo -e "${RED}Error: Could not find orchestrator pod in namespace $NAMESPACE${NC}"
    exit 1
fi

echo "Found pod: $POD"
echo "Executing Alembic migration..."

kubectl exec -it "$POD" -n "$NAMESPACE" -- /bin/bash -c "cd /app/backend && alembic upgrade head"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Migration completed successfully${NC}"
else
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
fi
