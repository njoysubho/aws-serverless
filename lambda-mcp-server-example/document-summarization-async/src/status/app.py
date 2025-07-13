import json
import boto3
import os
import logging
from boto3.dynamodb.conditions import Key

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Get job status and results
    """
    try:
        # Extract job ID from path parameters
        job_id = event['pathParameters']['jobId']
        
        if not job_id:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Job ID is required'})
            }
        
        # Get job from DynamoDB
        jobs_table = dynamodb.Table(os.environ['JOBS_TABLE'])
        response = jobs_table.get_item(Key={'jobId': job_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Job not found'})
            }
        
        job = response['Item']
        
        # Prepare response based on job status
        response_data = {
            'jobId': job['jobId'],
            'status': job['status'],
            'createdAt': job['createdAt'],
            'updatedAt': job['updatedAt']
        }
        
        # Add completion details if job is completed
        if job['status'] == 'completed':
            response_data.update({
                'summary': job.get('summary', ''),
                'completedAt': job.get('completedAt', '')
            })
        
        # Add error details if job failed
        if job['status'] == 'failed':
            response_data['errorMessage'] = job.get('errorMessage', 'Unknown error')
        
        # Add progress indicator for processing jobs
        if job['status'] == 'processing':
            response_data['message'] = 'Your document is being processed. Please check back in a few moments.'
        
        if job['status'] == 'queued':
            response_data['message'] = 'Your document is queued for processing.'
        
        logger.info(f"Retrieved job status: {job_id} - {job['status']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error retrieving job status: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }