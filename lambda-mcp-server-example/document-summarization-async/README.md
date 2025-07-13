# Document Summarization with External LLM - Serverless Pattern

This project demonstrates a **serverless document summarization application** using AWS Lambda and external LLM APIs (OpenAI). It implements an **asynchronous processing pattern** that's perfect for document processing workloads.

## 🏗️ Architecture

```
User → API Gateway → Lambda (Upload) → SQS → Lambda (Processor) → OpenAI API
       ↓              ↓                 ↓              ↓
   Document      DynamoDB           Processing      DynamoDB
   (Response)    (Job Status)       Queue          (Results)
                     ↓                               ↓
                 Lambda (Status)                EventBridge
                     ↓                               ↓
                 User Polling                  Notifications
```

## ✨ Key Features

- **Asynchronous Processing**: Handle documents of any size without timeout issues
- **External LLM Integration**: Uses OpenAI API (easily adaptable to other providers)
- **Job Tracking**: Real-time status updates via DynamoDB
- **Scalable Queue**: SQS handles processing load with dead letter queues
- **Event-Driven**: EventBridge notifications for job completion
- **RESTful API**: Clean HTTP endpoints for upload and status checking

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- AWS SAM CLI installed
- OpenAI API key
- Python 3.13+

## 🚀 Quick Start

1. **Clone and navigate to the project**:
   ```bash
   cd document-summarization-async
   ```

2. **Set your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Deploy the application**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Test the API**:
   ```bash
   # Upload a document
   curl -X POST https://your-api-url/prod/upload \
     -H "Content-Type: application/json" \
     -d '{
       "document": "This is a sample document that needs to be summarized...",
       "type": "text",
       "summary_length": "medium"
     }'
   
   # Check job status (use jobId from upload response)
   curl https://your-api-url/prod/status/your-job-id
   ```

## 🔧 API Endpoints

### POST /upload
Upload a document for summarization.

**Request Body**:
```json
{
  "document": "Document content or base64 encoded file",
  "type": "text|pdf|docx",
  "summary_length": "short|medium|long"
}
```

**Response**:
```json
{
  "jobId": "uuid-string",
  "status": "queued",
  "message": "Document queued for processing"
}
```

### GET /status/{jobId}
Check the processing status of a job.

**Response (Processing)**:
```json
{
  "jobId": "uuid-string",
  "status": "processing",
  "createdAt": "2024-01-01T12:00:00Z",
  "updatedAt": "2024-01-01T12:01:00Z",
  "message": "Your document is being processed..."
}
```

**Response (Completed)**:
```json
{
  "jobId": "uuid-string",
  "status": "completed",
  "summary": "Generated summary text...",
  "createdAt": "2024-01-01T12:00:00Z",
  "completedAt": "2024-01-01T12:02:00Z"
}
```

## 🎯 Why This Serverless Pattern Works for LLM Applications

### ✅ **Perfect for External LLMs**
- **No Model Storage**: External APIs eliminate Lambda's storage constraints
- **No Cold Start Issues**: No large models to load
- **Cost Effective**: Pay only for API calls and Lambda execution time
- **Always Updated**: External services provide latest model versions

### ✅ **Scalability Benefits**
- **Auto Scaling**: Lambda scales automatically with demand
- **Queue Management**: SQS handles traffic spikes gracefully
- **Parallel Processing**: Multiple documents processed simultaneously
- **Resource Optimization**: Each function optimized for its specific task

### ✅ **Reliability Features**
- **Error Handling**: Dead letter queues for failed jobs
- **Job Persistence**: DynamoDB stores all job states
- **Retry Logic**: Built-in SQS retry mechanisms
- **Monitoring**: CloudWatch logs and metrics

## 🔧 Advanced Configuration

### Environment Variables
- `OPENAI_API_KEY`: Your OpenAI API key
- `JOBS_TABLE`: DynamoDB table name (auto-configured)
- `PROCESSING_QUEUE`: SQS queue URL (auto-configured)
- `DOCUMENTS_BUCKET`: S3 bucket name (auto-configured)

### Customization Options

1. **Different LLM Providers**:
   - Replace OpenAI calls in `processor/app.py`
   - Update API key configuration
   - Modify prompt formatting

2. **Document Types**:
   - Add PDF processing with PyPDF2
   - Add DOCX processing with python-docx
   - Implement OCR for images

3. **Notification Methods**:
   - Email via SES
   - Slack webhooks
   - WebSocket for real-time updates
   - Mobile push notifications

## 📊 Monitoring & Troubleshooting

### CloudWatch Logs
- Check function logs: `/aws/lambda/document-summary-*`
- Monitor API Gateway logs
- Track SQS queue metrics

### Common Issues
1. **OpenAI API Rate Limits**: Implement exponential backoff
2. **Large Documents**: Consider chunking for very large files
3. **Queue Visibility**: Adjust timeout if processing takes longer

## 💰 Cost Optimization

- **Lambda**: Pay per request (typically $0.0000002 per request)
- **API Gateway**: $3.50 per million requests
- **DynamoDB**: Pay per read/write (On-Demand mode)
- **SQS**: $0.40 per million requests
- **S3**: Standard storage rates
- **External LLM**: Based on provider's pricing

## 🧹 Cleanup

```bash
sam delete
```

## 🔗 Additional Serverless Patterns

This architecture can be extended with:
- **Step Functions** for complex workflows
- **EventBridge** for event-driven integrations  
- **WebSocket API** for real-time status updates
- **CloudFront** for global API distribution
- **Cognito** for user authentication

---

This serverless pattern provides a production-ready foundation for document summarization applications using external LLMs, with excellent scalability, reliability, and cost-effectiveness.