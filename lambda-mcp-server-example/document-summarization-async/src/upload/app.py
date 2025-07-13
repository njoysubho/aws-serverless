import json
import boto3
import uuid
import base64
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')

def lambda_handler(event, context):
    try:
        # Parse request
        body = json.loads(event['body'])
        
        # Extract document content and metadata
        document_content = body.get('document')  # Base64 encoded or text
        document_type = body.get('type', 'text')  # text, pdf, docx
        summary_length = body.get('summary_length', 'medium')  # short, medium, long
        
        if not document_content:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Document content is required'})
            }
        
        # Generate job ID
        job_id = str(uuid.uuid4())
        
        # Store document in S3
        bucket_name = os.environ['DOCUMENTS_BUCKET']
        s3_key = f"documents/{job_id}.{document_type}"
        
        if document_type == 'text':
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=document_content,
                ContentType='text/plain'
            )
        else:
            # Assume base64 encoded for other types
            document_bytes = base64.b64decode(document_content)
            s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=document_bytes,
                ContentType=f'application/{document_type}'
            )
        
        # Create job record in DynamoDB
        jobs_table = dynamodb.Table(os.environ['JOBS_TABLE'])
        jobs_table.put_item(
            Item={
                'jobId': job_id,
                'status': 'queued',
                'documentType': document_type,
                'summaryLength': summary_length,
                's3Key': s3_key,
                'createdAt': datetime.utcnow().isoformat(),
                'updatedAt': datetime.utcnow().isoformat()
            }
        )
        
        # Send message to processing queue
        sqs.send_message(
            QueueUrl=os.environ['PROCESSING_QUEUE'],
            MessageBody=json.dumps({
                'jobId': job_id,
                's3Key': s3_key,
                'documentType': document_type,
                'summaryLength': summary_length
            })
        )
        
        logger.info(f"Document upload queued successfully: {job_id}")
        
        return {
            'statusCode': 202,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'jobId': job_id,
                'status': 'queued',
                'message': 'Document queued for processing'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }