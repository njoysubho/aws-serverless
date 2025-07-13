import json
import boto3
import os
import logging
from datetime import datetime
import openai
from typing import Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
eventbridge = boto3.client('events')

def lambda_handler(event, context):
    """
    Process documents with external LLM (OpenAI)
    """
    
    for record in event['Records']:
        try:
            # Parse SQS message
            message_body = json.loads(record['body'])
            job_id = message_body['jobId']
            s3_key = message_body['s3Key']
            document_type = message_body['documentType']
            summary_length = message_body['summaryLength']
            
            logger.info(f"Processing job: {job_id}")
            
            # Update job status to processing
            update_job_status(job_id, 'processing')
            
            # Get document from S3
            document_content = get_document_from_s3(s3_key)
            
            # Process with external LLM
            summary = summarize_with_openai(document_content, summary_length)
            
            # Update job with results
            update_job_with_results(job_id, summary)
            
            # Send completion event
            send_completion_event(job_id, 'completed')
            
            logger.info(f"Successfully processed job: {job_id}")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            
            # Update job status to failed
            update_job_status(job_id, 'failed', str(e))
            send_completion_event(job_id, 'failed')

def get_document_from_s3(s3_key: str) -> str:
    """Retrieve document content from S3"""
    try:
        bucket_name = os.environ['DOCUMENTS_BUCKET']
        response = s3.get_object(Bucket=bucket_name, Key=s3_key)
        
        if s3_key.endswith('.txt'):
            return response['Body'].read().decode('utf-8')
        else:
            # For PDF/DOCX, you'd need additional processing here
            # For now, treating as text
            return response['Body'].read().decode('utf-8')
            
    except Exception as e:
        logger.error(f"Error retrieving document from S3: {str(e)}")
        raise

def summarize_with_openai(document_content: str, summary_length: str) -> str:
    """Summarize document using OpenAI API"""
    try:
        # Initialize OpenAI client
        openai.api_key = os.environ['OPENAI_API_KEY']
        
        # Define length parameters
        length_params = {
            'short': '2-3 sentences',
            'medium': '1-2 paragraphs',
            'long': '3-4 paragraphs'
        }
        
        length_instruction = length_params.get(summary_length, '1-2 paragraphs')
        
        # Create prompt
        prompt = f"""
        Please summarize the following document in {length_instruction}. 
        Focus on the key points and main ideas:

        {document_content}
        """
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # or gpt-4
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that creates concise, accurate summaries of documents."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        logger.info("Successfully generated summary with OpenAI")
        return summary
        
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {str(e)}")
        raise

def update_job_status(job_id: str, status: str, error_message: str = None):
    """Update job status in DynamoDB"""
    try:
        jobs_table = dynamodb.Table(os.environ['JOBS_TABLE'])
        
        update_expression = "SET #status = :status, updatedAt = :updated_at"
        expression_values = {
            ':status': status,
            ':updated_at': datetime.utcnow().isoformat()
        }
        
        if error_message:
            update_expression += ", errorMessage = :error"
            expression_values[':error'] = error_message
        
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues=expression_values
        )
        
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        raise

def update_job_with_results(job_id: str, summary: str):
    """Update job with summary results"""
    try:
        jobs_table = dynamodb.Table(os.environ['JOBS_TABLE'])
        
        jobs_table.update_item(
            Key={'jobId': job_id},
            UpdateExpression="SET #status = :status, summary = :summary, completedAt = :completed_at, updatedAt = :updated_at",
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':summary': summary,
                ':completed_at': datetime.utcnow().isoformat(),
                ':updated_at': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating job with results: {str(e)}")
        raise

def send_completion_event(job_id: str, status: str):
    """Send completion event to EventBridge"""
    try:
        eventbridge.put_events(
            Entries=[
                {
                    'Source': 'document.summarization',
                    'DetailType': 'Job Status Change',
                    'Detail': json.dumps({
                        'jobId': job_id,
                        'status': status,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                }
            ]
        )
        
        logger.info(f"Sent completion event for job: {job_id}")
        
    except Exception as e:
        logger.error(f"Error sending completion event: {str(e)}")
        # Don't raise - this is not critical for job processing