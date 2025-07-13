# Document Summarization Serverless Application Makefile

.PHONY: help install build deploy deploy-guided test clean logs validate local-test

# Default target
help:
	@echo "📋 Available commands:"
	@echo ""
	@echo "🔧 Setup & Build:"
	@echo "  make install       - Install dependencies"
	@echo "  make build         - Build SAM application"
	@echo "  make validate      - Validate SAM template"
	@echo ""
	@echo "🚀 Deployment:"
	@echo "  make deploy-guided - Deploy with guided setup (first time)"
	@echo "  make deploy        - Deploy with existing config"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  make test          - Run integration tests"
	@echo "  make local-test    - Test Lambda functions locally"
	@echo ""
	@echo "📊 Monitoring:"
	@echo "  make logs          - Tail CloudWatch logs"
	@echo "  make metrics       - Show application metrics"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make delete        - Delete entire stack"
	@echo ""
	@echo "⚙️  Configuration:"
	@echo "  OPENAI_API_KEY     - Set your OpenAI API key"
	@echo "  STACK_NAME         - Override stack name (default: doc-summary-app)"
	@echo "  AWS_REGION         - Override AWS region"

# Configuration
STACK_NAME ?= doc-summary-app
AWS_REGION ?= us-east-1

# Check for required environment variables
check-env:
	@if [ -z "$(OPENAI_API_KEY)" ]; then \
		echo "❌ Error: OPENAI_API_KEY environment variable is required"; \
		echo "Set it with: export OPENAI_API_KEY='your-api-key'"; \
		exit 1; \
	fi

# Install dependencies
install:
	@echo "📦 Installing Python dependencies..."
	@for dir in src/*/; do \
		if [ -f "$$dir/requirements.txt" ]; then \
			echo "Installing dependencies for $$dir"; \
			pip install -r "$$dir/requirements.txt" -t "$$dir" --upgrade; \
		fi; \
	done
	@echo "✅ Dependencies installed successfully"

# Validate SAM template
validate:
	@echo "🔍 Validating SAM template..."
	@sam validate
	@echo "✅ Template validation successful"

# Build application
build: validate
	@echo "🔨 Building SAM application..."
	@sam build
	@echo "✅ Build completed successfully"

# Deploy with guided setup (first time)
deploy-guided: check-env build
	@echo "🚀 Deploying with guided setup..."
	@sam deploy --guided \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION) \
		--parameter-overrides \
			OpenAIApiKey="$(OPENAI_API_KEY)" \
		--capabilities CAPABILITY_IAM
	@echo "✅ Deployment completed successfully"
	@make show-endpoints

# Deploy with existing configuration
deploy: check-env build
	@echo "🔄 Deploying with existing configuration..."
	@sam deploy \
		--parameter-overrides OpenAIApiKey="$(OPENAI_API_KEY)"
	@echo "✅ Deployment completed successfully"
	@make show-endpoints

# Show API endpoints after deployment
show-endpoints:
	@echo ""
	@echo "🔗 API Endpoints:"
	@aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION) \
		--query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayUrl`].OutputValue' \
		--output text | xargs -I {} echo "  API Base URL: {}"
	@echo ""
	@echo "📖 Usage Examples:"
	@echo "  Upload document:"
	@echo "    curl -X POST {API_URL}/upload \\"
	@echo "      -H 'Content-Type: application/json' \\"
	@echo "      -d '{\"document\":\"Your text here\",\"type\":\"text\",\"summary_length\":\"medium\"}'"
	@echo ""
	@echo "  Check status:"
	@echo "    curl {API_URL}/status/{job_id}"

# Test the deployed application
test:
	@echo "🧪 Running integration tests..."
	@./test-api.sh
	@echo "✅ Tests completed"

# Local testing with SAM
local-test: build
	@echo "🏠 Testing Lambda functions locally..."
	@echo "Testing upload function..."
	@sam local invoke UploadFunction -e events/upload-test.json
	@echo ""
	@echo "Testing status function..."
	@sam local invoke StatusFunction -e events/status-test.json
	@echo "✅ Local tests completed"

# Create test events
create-test-events:
	@echo "📝 Creating test events..."
	@mkdir -p events
	@echo '{"body": "{\"document\":\"This is a test document that needs to be summarized.\",\"type\":\"text\",\"summary_length\":\"short\"}", "httpMethod": "POST", "pathParameters": null}' > events/upload-test.json
	@echo '{"pathParameters": {"jobId": "test-job-123"}, "httpMethod": "GET"}' > events/status-test.json
	@echo "✅ Test events created in events/ directory"

# Start local API
local-api: build
	@echo "🏠 Starting local API server..."
	@echo "API will be available at: http://127.0.0.1:3000"
	@sam local start-api --port 3000

# Tail CloudWatch logs
logs:
	@echo "📊 Tailing CloudWatch logs (Ctrl+C to stop)..."
	@sam logs --stack-name $(STACK_NAME) --tail

# Show application metrics
metrics:
	@echo "📈 Application Metrics:"
	@echo ""
	@echo "🔍 API Gateway Metrics:"
	@aws cloudwatch get-metric-statistics \
		--namespace AWS/ApiGateway \
		--metric-name Count \
		--dimensions Name=ApiName,Value=$(STACK_NAME) \
		--start-time $(shell date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
		--end-time $(shell date -u +%Y-%m-%dT%H:%M:%S) \
		--period 3600 \
		--statistics Sum \
		--region $(AWS_REGION) \
		--query 'Datapoints[0].Sum' --output text | xargs -I {} echo "  Total Requests (last hour): {}"
	@echo ""
	@echo "⚡ Lambda Metrics:"
	@aws cloudwatch get-metric-statistics \
		--namespace AWS/Lambda \
		--metric-name Invocations \
		--dimensions Name=FunctionName,Value=$(STACK_NAME)-UploadFunction \
		--start-time $(shell date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
		--end-time $(shell date -u +%Y-%m-%dT%H:%M:%S) \
		--period 3600 \
		--statistics Sum \
		--region $(AWS_REGION) \
		--query 'Datapoints[0].Sum' --output text | xargs -I {} echo "  Upload Function Invocations: {}"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf .aws-sam/
	@rm -rf events/
	@find src/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find src/ -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean completed"

# Delete the entire stack
delete:
	@echo "🗑️  Deleting stack..."
	@echo "⚠️  This will delete all resources. Continue? [y/N]"
	@read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		sam delete --stack-name $(STACK_NAME) --region $(AWS_REGION) --no-prompts; \
		echo "✅ Stack deleted successfully"; \
	else \
		echo "❌ Deletion cancelled"; \
	fi

# Development helpers
dev-setup: install create-test-events
	@echo "🔧 Development environment setup completed"
	@echo "Run 'make local-api' to start local development server"

# Quick deploy for development
dev-deploy: build deploy show-endpoints

# Production deploy with confirmation
prod-deploy:
	@echo "🚨 Production Deployment"
	@echo "Stack: $(STACK_NAME)"
	@echo "Region: $(AWS_REGION)"
	@echo "Continue with production deployment? [y/N]"
	@read -r REPLY; \
	if [ "$$REPLY" = "y" ] || [ "$$REPLY" = "Y" ]; then \
		make deploy; \
	else \
		echo "❌ Deployment cancelled"; \
	fi

# Show stack info
info:
	@echo "📋 Stack Information:"
	@echo "  Stack Name: $(STACK_NAME)"
	@echo "  Region: $(AWS_REGION)"
	@echo "  Status:" 
	@aws cloudformation describe-stacks \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION) \
		--query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "    Stack not found"
	@echo ""
	@echo "📊 Resources:"
	@aws cloudformation list-stack-resources \
		--stack-name $(STACK_NAME) \
		--region $(AWS_REGION) \
		--query 'StackResourceSummaries[].{Type:ResourceType,Status:ResourceStatus}' \
		--output table 2>/dev/null || echo "    No resources found"