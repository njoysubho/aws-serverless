import json
import boto3
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# You can add SNS, SES, or other notification services here
sns = boto3.client('sns')

def lambda_handler(event, context):
    """
    Handle job completion notifications via DynamoDB Streams
    """
    try:
        for record in event['Records']:
            if record['eventName'] == 'MODIFY':
                # Extract job information
                new_image = record['dynamodb']['NewImage']
                old_image = record['dynamodb'].get('OldImage', {})
                
                job_id = new_image['jobId']['S']
                new_status = new_image['status']['S']
                old_status = old_image.get('status', {}).get('S', '')
                
                # Only process status changes to completed or failed
                if new_status in ['completed', 'failed'] and new_status != old_status:
                    logger.info(f"Job {job_id} status changed to {new_status}")
                    
                    # Here you can implement various notification methods:
                    
                    # 1. Email notification (using SES)
                    # send_email_notification(job_id, new_status, new_image)
                    
                    # 2. SMS notification (using SNS)
                    # send_sms_notification(job_id, new_status)
                    
                    # 3. Slack/Teams webhook
                    # send_slack_notification(job_id, new_status, new_image)
                    
                    # 4. Push notification to mobile app
                    # send_push_notification(job_id, new_status)
                    
                    # 5. WebSocket notification for real-time updates
                    # send_websocket_notification(job_id, new_status, new_image)
                    
                    # For demo, just log the completion
                    log_completion(job_id, new_status, new_image)
                    
    except Exception as e:
        logger.error(f"Error processing notification: {str(e)}")

def log_completion(job_id: str, status: str, job_data: dict):
    """Log job completion details"""
    try:
        message = f"Document summarization job {job_id} {status}"
        
        if status == 'completed':
            summary_preview = job_data.get('summary', {}).get('S', '')[:100] + '...'
            message += f". Summary preview: {summary_preview}"
        elif status == 'failed':
            error_message = job_data.get('errorMessage', {}).get('S', 'Unknown error')
            message += f". Error: {error_message}"
        
        logger.info(message)
        
        # You could also write to CloudWatch custom metrics here
        # cloudwatch = boto3.client('cloudwatch')
        # cloudwatch.put_metric_data(...)
        
    except Exception as e:
        logger.error(f"Error logging completion: {str(e)}")

def send_email_notification(job_id: str, status: str, job_data: dict):
    """Send email notification using SES (implement as needed)"""
    # Example implementation:
    # ses = boto3.client('ses')
    # ses.send_email(...)
    pass

def send_slack_notification(job_id: str, status: str, job_data: dict):
    """Send Slack notification via webhook (implement as needed)"""
    # Example implementation:
    # import requests
    # webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    # requests.post(webhook_url, json={...})
    pass

def send_websocket_notification(job_id: str, status: str, job_data: dict):
    """Send real-time notification via API Gateway WebSocket (implement as needed)"""
    # Example implementation:
    # apigatewaymanagementapi = boto3.client('apigatewaymanagementapi')
    # apigatewaymanagementapi.post_to_connection(...)
    pass