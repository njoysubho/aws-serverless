# SNS-SQS-Lambda-DynamoDB Fanout Architecture

This project implements a Java AWS Lambda function that processes messages from an SNS-SQS fanout architecture and stores them in DynamoDB.

## Architecture

```
SNS Topic → SQS Queue → Lambda Function → DynamoDB Table
                ↓
        Dead Letter Queue (DLQ)
```

## Components

- **SNS Topic**: Receives messages and fans them out to subscribers
- **SQS Queue**: Buffers messages and triggers the Lambda function
- **Lambda Function**: Processes messages and stores them in DynamoDB
- **DynamoDB Table**: Stores the processed messages
- **Dead Letter Queue**: Handles failed messages after retry attempts

## Message Format

The Lambda function expects messages with the following JSON structure:

```json
{
  "id": "unique-message-id",
  "name": "message-name"
}
```

## Prerequisites

- Java 17 or later
- Maven 3.6 or later
- AWS CLI configured with appropriate permissions
- AWS SAM CLI (for deployment)

## Building the Project

```bash
# Clean and compile
mvn clean compile

# Run tests
mvn test

# Package the application
mvn package
```

## Deployment

### Using AWS SAM

1. **Build the SAM application:**
   ```bash
   sam build
   ```

2. **Deploy the application:**
   ```bash
   sam deploy --guided
   ```

   Follow the prompts to configure:
   - Stack name
   - AWS Region
   - Environment (dev/prod/etc.)
   - Confirm changes before deploy

3. **For subsequent deployments:**
   ```bash
   sam deploy
   ```

### Manual Deployment Steps

If you prefer to deploy manually:

1. **Create the DynamoDB table**
2. **Create the SNS topic**
3. **Create the SQS queue and dead letter queue**
4. **Set up the SNS subscription to SQS**
5. **Deploy the Lambda function**
6. **Configure the SQS trigger for Lambda**

## Environment Variables

The Lambda function requires the following environment variables:

- `TABLE_NAME`: Name of the DynamoDB table
- `AWS_REGION`: AWS region (automatically set by Lambda runtime)

## Testing

### Unit Tests

Run unit tests with:
```bash
mvn test
```

### Integration Testing

1. **Send a test message to SNS:**
   ```bash
   aws sns publish \
     --topic-arn arn:aws:sns:region:account:topic-name \
     --message '{"id":"test-123","name":"Test Message"}'
   ```

2. **Check DynamoDB for the stored message:**
   ```bash
   aws dynamodb get-item \
     --table-name your-table-name \
     --key '{"id":{"S":"test-123"}}'
   ```

3. **Monitor Lambda logs:**
   ```bash
   aws logs tail /aws/lambda/your-function-name --follow
   ```

## Monitoring and Troubleshooting

### CloudWatch Metrics

Monitor the following metrics:
- Lambda invocations, errors, and duration
- SQS queue depth and age of oldest message
- DynamoDB read/write capacity and throttles

### Common Issues

1. **Messages not processing:**
   - Check SQS queue visibility timeout (should be 3x Lambda timeout)
   - Verify IAM permissions for Lambda to access DynamoDB
   - Check Lambda function logs for errors

2. **Messages going to DLQ:**
   - Review Lambda function logs for processing errors
   - Verify message format matches expected schema
   - Check DynamoDB table capacity and throttling

3. **High Lambda errors:**
   - Ensure DynamoDB table exists and is accessible
   - Verify network connectivity if Lambda is in VPC
   - Check for malformed JSON in messages

### Viewing Logs

```bash
# View recent Lambda logs
sam logs -n MessageProcessorFunction --tail

# View logs for specific time range
sam logs -n MessageProcessorFunction --start-time '1hour ago' --end-time '30min ago'
```

## Configuration

### Batch Processing

The SQS trigger is configured to:
- Process up to 10 messages per batch
- Wait up to 5 seconds to collect messages for batching
- Retry failed batches with exponential backoff

### Dead Letter Queue

Messages are sent to DLQ after 3 failed processing attempts.

### DynamoDB Table

- Uses on-demand billing mode
- Point-in-time recovery enabled
- DynamoDB Streams enabled for change tracking

## Security

The Lambda function has minimal IAM permissions:
- Read from SQS queue
- Write to DynamoDB table
- Write logs to CloudWatch

## Cost Optimization

- Uses ARM64 architecture for better price-performance
- On-demand billing for DynamoDB
- Batch processing to reduce Lambda invocations

## Development

### Local Testing

1. **Build the project:**
   ```bash
   mvn package
   ```

2. **Create a test event file (test-event.json):**
   ```json
   {
     "Records": [
       {
         "messageId": "test-message-id",
         "receiptHandle": "test-receipt-handle",
         "body": "{\"id\":\"123\",\"name\":\"Test Message\"}",
         "attributes": {},
         "messageAttributes": {},
         "md5OfBody": "test-md5",
         "eventSource": "aws:sqs",
         "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:test-queue",
         "awsRegion": "us-east-1"
       }
     ]
   }
   ```

3. **Test locally with SAM:**
   ```bash
   sam local invoke MessageProcessorFunction --event test-event.json
   ```

### Adding New Features

1. Update the `Message` model class
2. Modify the `DynamoDbService` for new operations
3. Update the Lambda handler logic
4. Add corresponding tests
5. Update the SAM template if infrastructure changes are needed

## Cleanup

To delete all AWS resources:

```bash
sam delete
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.