import boto3

def get_secret(secret_name):
    # Create a Systems Manager client (Parameter Store is part of Systems Manager)
    session = boto3.session.Session()
    client = session.client(
        service_name='ssm',  # Changed from 'secretsmanager' to 'ssm'
        region_name="eu-west-1"
    )
    try:
        # Get parameter from Parameter Store
        response = client.get_parameter(
            Name=secret_name,
            WithDecryption=True  # This will decrypt SecureString parameters automatically
        )
    except client.exceptions.ParameterNotFound as e:
        # Parameter not found
        raise e
    except Exception as e:
        # For other exceptions
        raise e

    # Extract the parameter value
    secret = response['Parameter']['Value']
    return secret