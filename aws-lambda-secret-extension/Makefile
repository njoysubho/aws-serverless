# Makefile for automating build and deployment tasks

# Define variables
BUCKET_NAME = sab-lambda-artifact
FUNCTION_NAME = lambda-secret-extension
JAR_FILE = aws-lambda-secret-extension-1.0.0-SNAPSHOT.jar

# Default target
all: build s3copy createlambda

# Maven build
build:
	mvn clean install


# Copy the zip file to S3
s3copy:
	aws s3 cp target/$(JAR_FILE) s3://$(BUCKET_NAME)/$(JAR_FILE)

# Create the AWS Lambda function
createlambda:
	aws lambda update-function-code --function-name $(FUNCTION_NAME) \
    --region eu-west-1 \
    --s3-bucket=$(BUCKET_NAME) \
    --s3-key=$(JAR_FILE)

secretlayer:
	aws lambda update-function-configuration --function-name $(FUNCTION_NAME) \
	--region eu-west-1 \
	--layers arn:aws:lambda:eu-central-1:187925254637:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11

.PHONY: build s3copy createlambda all
