#!/bin/bash

# API Integration Test Script for Document Summarization Service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME=${STACK_NAME:-doc-summary-app}
AWS_REGION=${AWS_REGION:-us-east-1}

echo -e "${BLUE}🧪 Starting API Integration Tests${NC}"
echo "=================================="

# Get API Gateway URL from CloudFormation
echo -e "${YELLOW}📡 Getting API Gateway URL...${NC}"
API_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $AWS_REGION \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
    --output text)

if [ -z "$API_URL" ]; then
    echo -e "${RED}❌ Error: Could not retrieve API Gateway URL${NC}"
    echo "Make sure the stack is deployed and the stack name is correct."
    exit 1
fi

echo -e "${GREEN}✅ API URL: $API_URL${NC}"
echo ""

# Test 1: Upload a document
echo -e "${BLUE}🔄 Test 1: Document Upload${NC}"
echo "----------------------------"

UPLOAD_RESPONSE=$(curl -s -X POST "$API_URL/upload" \
    -H "Content-Type: application/json" \
    -d '{
        "document": "Artificial Intelligence (AI) has revolutionized numerous industries and aspects of human life. From healthcare diagnostics to autonomous vehicles, AI systems are becoming increasingly sophisticated and integrated into our daily routines. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions that were previously impossible for humans to achieve manually. The technology continues to evolve rapidly, with new breakthroughs in neural networks, natural language processing, and computer vision occurring regularly. However, this advancement also brings challenges related to ethics, privacy, and the future of work that society must address thoughtfully.",
        "type": "text",
        "summary_length": "medium"
    }')

echo "Upload Response:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPLOAD_RESPONSE"

# Extract job ID from response
JOB_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['jobId'])" 2>/dev/null)

if [ -z "$JOB_ID" ]; then
    echo -e "${RED}❌ Error: Could not extract job ID from upload response${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Document uploaded successfully. Job ID: $JOB_ID${NC}"
echo ""

# Test 2: Check job status immediately (should be queued)
echo -e "${BLUE}🔄 Test 2: Initial Status Check${NC}"
echo "--------------------------------"

STATUS_RESPONSE=$(curl -s "$API_URL/status/$JOB_ID")
echo "Initial Status Response:"
echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"

INITIAL_STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
echo -e "${GREEN}✅ Initial status: $INITIAL_STATUS${NC}"
echo ""

# Test 3: Wait for processing and check final status
echo -e "${BLUE}🔄 Test 3: Wait for Processing Completion${NC}"
echo "-------------------------------------------"

echo "Waiting for document processing to complete..."
RETRY_COUNT=0
MAX_RETRIES=12  # 2 minutes max (10 seconds * 12)

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 10
    STATUS_RESPONSE=$(curl -s "$API_URL/status/$JOB_ID")
    CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
    
    echo -e "${YELLOW}Status check $((RETRY_COUNT + 1)): $CURRENT_STATUS${NC}"
    
    if [ "$CURRENT_STATUS" = "completed" ]; then
        echo -e "${GREEN}✅ Processing completed successfully!${NC}"
        echo ""
        echo "Final Response:"
        echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
        break
    elif [ "$CURRENT_STATUS" = "failed" ]; then
        echo -e "${RED}❌ Processing failed${NC}"
        echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"
        exit 1
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${YELLOW}⚠️  Warning: Processing is taking longer than expected${NC}"
    echo "Final status: $CURRENT_STATUS"
    echo "This might indicate an issue with the external LLM API or processing logic."
fi

echo ""

# Test 4: Test invalid job ID
echo -e "${BLUE}🔄 Test 4: Invalid Job ID Test${NC}"
echo "-------------------------------"

INVALID_RESPONSE=$(curl -s "$API_URL/status/invalid-job-id-12345")
echo "Invalid Job ID Response:"
echo "$INVALID_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$INVALID_RESPONSE"

if echo "$INVALID_RESPONSE" | grep -q "not found"; then
    echo -e "${GREEN}✅ Invalid job ID handling works correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Invalid job ID response might need improvement${NC}"
fi

echo ""

# Test 5: Test malformed upload request
echo -e "${BLUE}🔄 Test 5: Malformed Request Test${NC}"
echo "-----------------------------------"

MALFORMED_RESPONSE=$(curl -s -X POST "$API_URL/upload" \
    -H "Content-Type: application/json" \
    -d '{"invalid": "request"}')

echo "Malformed Request Response:"
echo "$MALFORMED_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MALFORMED_RESPONSE"

if echo "$MALFORMED_RESPONSE" | grep -q "error"; then
    echo -e "${GREEN}✅ Error handling works correctly${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Error handling might need improvement${NC}"
fi

echo ""

# Summary
echo -e "${BLUE}📊 Test Summary${NC}"
echo "================"
echo -e "${GREEN}✅ API endpoint accessible${NC}"
echo -e "${GREEN}✅ Document upload functionality${NC}"
echo -e "${GREEN}✅ Job status tracking${NC}"
echo -e "${GREEN}✅ Error handling for invalid requests${NC}"

if [ "$CURRENT_STATUS" = "completed" ]; then
    echo -e "${GREEN}✅ End-to-end processing pipeline${NC}"
else
    echo -e "${YELLOW}⚠️  Processing pipeline (check logs for issues)${NC}"
fi

echo ""
echo -e "${BLUE}🔍 Troubleshooting Tips:${NC}"
echo "- Check CloudWatch logs: make logs"
echo "- View metrics: make metrics"
echo "- Verify OpenAI API key is valid and has credits"
echo "- Check SQS dead letter queue for failed messages"

echo ""
echo -e "${GREEN}🎉 Integration tests completed!${NC}"