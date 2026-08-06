#!/bin/bash

################################################################################
# AIDI POC - API Test Script
# 
# This script provides sample cURL commands to test all AIDI endpoints
# 
# Usage:
#   ./test_api.sh                    # Interactive mode (prompts for actions)
#   ./test_api.sh health             # Run only health check
#   ./test_api.sh full               # Run all tests
#   ./test_api.sh classify           # Run classification test
#   ./test_api.sh explain            # Run explanation test
#
# Requirements:
#   - curl installed
#   - jq installed (for pretty JSON output, optional)
#   - AIDI API running on http://localhost:8000
#
################################################################################

set -e

# Configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
API_KEY_FILE="${API_KEY_FILE:-.aidi_api_key}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to print headers
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"
}

# Helper function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Helper function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Helper function to print info
print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Helper function to make requests
make_request() {
    local method=$1
    local endpoint=$2
    local data=$3
    local headers=${4:-""}
    
    if [ -z "$data" ]; then
        curl -s -X "$method" "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            $headers
    else
        curl -s -X "$method" "${BASE_URL}${endpoint}" \
            -H "Content-Type: application/json" \
            $headers \
            -d "$data"
    fi
}

# Test 1: Health Check
test_health() {
    print_header "TEST 1: Health Check"
    
    echo "Endpoint: GET /api/health"
    echo "Command:"
    echo "  curl -X GET \"${BASE_URL}/api/health\""
    echo ""
    echo "Response:"
    
    response=$(make_request GET "/api/health")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "healthy"; then
        print_success "API is healthy"
    else
        print_error "API health check failed"
        return 1
    fi
}

# Test 2: User Registration
test_register() {
    print_header "TEST 2: User Registration"
    
    echo "Endpoint: POST /api/auth/register"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/auth/register\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"email\": \"test@example.com\", \"username\": \"testuser\", \"password\": \"securepass123\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "email": "test@example.com",
        "username": "testuser",
        "password": "securepass123"
    }'
    
    response=$(make_request POST "/api/auth/register" "$data")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "test@example.com"; then
        print_success "User registered successfully"
    else
        print_error "User registration failed"
        # Try to handle duplicate user
        if echo "$response" | grep -q "already exists"; then
            print_info "User already exists (this is OK)"
        fi
    fi
}

# Test 3: User Login
test_login() {
    print_header "TEST 3: User Login"
    
    echo "Endpoint: POST /api/auth/login"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/auth/login\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"email\": \"test@example.com\", \"password\": \"securepass123\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "email": "test@example.com",
        "password": "securepass123"
    }'
    
    response=$(make_request POST "/api/auth/login" "$data")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "access_token"; then
        print_success "User logged in successfully"
    else
        print_error "User login failed"
        return 1
    fi
}

# Test 4: Create API Key
test_create_api_key() {
    print_header "TEST 4: Create API Key"
    
    echo "Endpoint: POST /api/auth/keys"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/auth/keys\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"name\": \"test-key\", \"email\": \"test@example.com\", \"password\": \"securepass123\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "name": "test-key",
        "email": "test@example.com",
        "password": "securepass123"
    }'
    
    response=$(make_request POST "/api/auth/keys" "$data")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    # Extract and save API key
    if command -v jq &> /dev/null; then
        api_key=$(echo "$response" | jq -r '.key' 2>/dev/null || echo "")
    else
        api_key=$(echo "$response" | grep -oP '"key":\s*"\K[^"]+' || echo "")
    fi
    
    if [ -n "$api_key" ] && [ "$api_key" != "null" ]; then
        echo "$api_key" > "$API_KEY_FILE"
        print_success "API key created and saved to $API_KEY_FILE"
        echo "API Key (first 50 chars): ${api_key:0:50}..."
    else
        print_error "Failed to extract API key"
        return 1
    fi
}

# Test 5: List API Keys
test_list_api_keys() {
    print_header "TEST 5: List API Keys"
    
    echo "Endpoint: GET /api/auth/keys"
    echo "Command:"
    echo "  curl -X GET \"${BASE_URL}/api/auth/keys\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"email\": \"test@example.com\", \"password\": \"securepass123\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "email": "test@example.com",
        "password": "securepass123"
    }'
    
    response=$(make_request GET "/api/auth/keys" "$data")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "test-key"; then
        print_success "API keys listed successfully"
    fi
}

# Test 6: Process Health
test_process_health() {
    print_header "TEST 6: Process Service Health"
    
    echo "Endpoint: GET /api/process/health"
    echo "Command:"
    echo "  curl -X GET \"${BASE_URL}/api/process/health\""
    echo ""
    echo "Response:"
    
    response=$(make_request GET "/api/process/health")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "tools_loaded"; then
        print_success "Process service is healthy"
    fi
}

# Test 7: Process - Classification Request
test_process_classify() {
    print_header "TEST 7: Process - Classification Request"
    
    # Load API key
    if [ ! -f "$API_KEY_FILE" ]; then
        print_error "API key file not found: $API_KEY_FILE"
        print_info "Run 'test_create_api_key' first or manually set the API key"
        return 1
    fi
    
    api_key=$(cat "$API_KEY_FILE")
    
    echo "Endpoint: POST /api/process"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/process\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -H \"X-API-Key: \${API_KEY}\" \\"
    echo "    -d '{\"prompt\": \"Classify the sentiment of this: This product is amazing!\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "prompt": "Classify the sentiment of this review: This product is amazing and exceeded all my expectations!"
    }'
    
    response=$(make_request POST "/api/process" "$data" "-H \"X-API-Key: $api_key\"")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "request_id"; then
        print_success "Classification request processed"
    else
        print_error "Classification request failed"
        echo "Note: This requires Ollama to be running"
    fi
}

# Test 8: Process - Explanation Request
test_process_explain() {
    print_header "TEST 8: Process - Explanation Request"
    
    # Load API key
    if [ ! -f "$API_KEY_FILE" ]; then
        print_error "API key file not found: $API_KEY_FILE"
        return 1
    fi
    
    api_key=$(cat "$API_KEY_FILE")
    
    echo "Endpoint: POST /api/process"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/process\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -H \"X-API-Key: \${API_KEY}\" \\"
    echo "    -d '{\"prompt\": \"Explain how neural networks work\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "prompt": "Explain how neural networks work in simple terms"
    }'
    
    response=$(make_request POST "/api/process" "$data" "-H \"X-API-Key: $api_key\"")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "request_id"; then
        print_success "Explanation request processed"
    else
        print_error "Explanation request failed"
    fi
}

# Test 9: Process - Code Request
test_process_code() {
    print_header "TEST 9: Process - Code Generation Request"
    
    # Load API key
    if [ ! -f "$API_KEY_FILE" ]; then
        print_error "API key file not found: $API_KEY_FILE"
        return 1
    fi
    
    api_key=$(cat "$API_KEY_FILE")
    
    echo "Endpoint: POST /api/process"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/process\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -H \"X-API-Key: \${API_KEY}\" \\"
    echo "    -d '{\"prompt\": \"Write a Python function to reverse a string\"}'"
    echo ""
    echo "Response:"
    
    data='{
        "prompt": "Write a Python function to reverse a string"
    }'
    
    response=$(make_request POST "/api/process" "$data" "-H \"X-API-Key: $api_key\"")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
}

# Test 10: Process - PII Redaction Test
test_process_pii() {
    print_header "TEST 10: Process - PII Redaction Test"
    
    # Load API key
    if [ ! -f "$API_KEY_FILE" ]; then
        print_error "API key file not found: $API_KEY_FILE"
        return 1
    fi
    
    api_key=$(cat "$API_KEY_FILE")
    
    echo "Endpoint: POST /api/process (with PII)"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/process\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -H \"X-API-Key: \${API_KEY}\" \\"
    echo "    -d '{\"prompt\": \"My email is john@example.com and phone is 555-1234\"}'"
    echo ""
    echo "Response (PII should be redacted):"
    
    data='{
        "prompt": "My email is john@example.com and my phone is 555-1234. Can you help me?"
    }'
    
    response=$(make_request POST "/api/process" "$data" "-H \"X-API-Key: $api_key\"")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "EMAIL_REDACTED"; then
        print_success "PII redaction is working"
    fi
}

# Test 11: Error - Invalid API Key
test_error_invalid_key() {
    print_header "TEST 11: Error - Invalid API Key"
    
    echo "Endpoint: POST /api/process"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/process\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -H \"X-API-Key: invalid_key_12345\" \\"
    echo "    -d '{\"prompt\": \"test\"}'"
    echo ""
    echo "Expected: 401 Unauthorized"
    echo "Response:"
    
    data='{"prompt": "test"}'
    response=$(make_request POST "/api/process" "$data" "-H \"X-API-Key: invalid_key_12345\"")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
    
    if echo "$response" | grep -q "401\|Unauthorized\|Invalid"; then
        print_success "Invalid API key correctly rejected"
    fi
}

# Test 12: Error - Missing API Key
test_error_missing_key() {
    print_header "TEST 12: Error - Missing API Key"
    
    echo "Endpoint: POST /api/process (without X-API-Key header)"
    echo "Command:"
    echo "  curl -X POST \"${BASE_URL}/api/process\" \\"
    echo "    -H \"Content-Type: application/json\" \\"
    echo "    -d '{\"prompt\": \"test\"}'"
    echo ""
    echo "Expected: 422 Validation Error"
    echo "Response:"
    
    data='{"prompt": "test"}'
    response=$(make_request POST "/api/process" "$data")
    
    if command -v jq &> /dev/null; then
        echo "$response" | jq '.'
    else
        echo "$response"
    fi
}

# Interactive menu
show_menu() {
    echo -e "\n${BLUE}AIDI API Test Menu${NC}\n"
    echo "1) Health Check"
    echo "2) Register User"
    echo "3) Login User"
    echo "4) Create API Key"
    echo "5) List API Keys"
    echo "6) Process Service Health"
    echo "7) Process - Classification"
    echo "8) Process - Explanation"
    echo "9) Process - Code Generation"
    echo "10) Process - PII Redaction Test"
    echo "11) Error - Invalid API Key"
    echo "12) Error - Missing API Key"
    echo "13) Run All Tests"
    echo "0) Exit"
    echo ""
}

# Run all tests
run_all_tests() {
    print_header "RUNNING ALL AIDI API TESTS"
    
    test_health || true
    test_register || true
    test_login || true
    test_create_api_key || true
    test_list_api_keys || true
    test_process_health || true
    test_process_classify || true
    test_process_explain || true
    test_process_code || true
    test_process_pii || true
    test_error_invalid_key || true
    test_error_missing_key || true
    
    print_header "ALL TESTS COMPLETE"
}

# Main script
main() {
    # Check if curl is installed
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed. Please install it first."
        exit 1
    fi
    
    # Handle command line arguments
    case "$1" in
        health)
            test_health
            ;;
        register)
            test_register
            ;;
        login)
            test_login
            ;;
        keys)
            test_create_api_key
            ;;
        list-keys)
            test_list_api_keys
            ;;
        process-health)
            test_process_health
            ;;
        classify)
            test_process_classify
            ;;
        explain)
            test_process_explain
            ;;
        code)
            test_process_code
            ;;
        pii)
            test_process_pii
            ;;
        error-invalid)
            test_error_invalid_key
            ;;
        error-missing)
            test_error_missing_key
            ;;
        full)
            run_all_tests
            ;;
        *)
            # Interactive mode
            while true; do
                show_menu
                read -p "Select option: " choice
                
                case $choice in
                    1) test_health ;;
                    2) test_register ;;
                    3) test_login ;;
                    4) test_create_api_key ;;
                    5) test_list_api_keys ;;
                    6) test_process_health ;;
                    7) test_process_classify ;;
                    8) test_process_explain ;;
                    9) test_process_code ;;
                    10) test_process_pii ;;
                    11) test_error_invalid_key ;;
                    12) test_error_missing_key ;;
                    13) run_all_tests ;;
                    0) 
                        print_info "Exiting..."
                        exit 0
                        ;;
                    *)
                        print_error "Invalid option. Please try again."
                        ;;
                esac
                
                read -p "Press Enter to continue..."
            done
            ;;
    esac
}

# Run main function
main "$@"
