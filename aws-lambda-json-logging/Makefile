# Makefile for automating build and deployment tasks

# Define variables
BUCKET_NAME = sab-lambda-artifact
FUNCTION_NAME = lambda-json-logging
JAR_FILE = aws-lambda-json-logging-1.0.0-SNAPSHOT.jar

# Default target
create: build s3copy createlambda
update: build s3copy updateLambda
# Maven build
build:
	mvn clean install


# Copy the zip file to S3
s3copy:
	aws s3 cp target/$(JAR_FILE) s3://$(BUCKET_NAME)/$(JAR_FILE)

# Create the AWS Lambda function
createlambda:
	aws lambda create-function --function-name $(FUNCTION_NAME) \
    	--code S3Bucket=$(BUCKET_NAME),S3Key=$(JAR_FILE) \
    	--handler com.sab.serverless.LambdaHandler::handleRequest \
    	--runtime java21 \
    	--region eu-west-1 \
    	--role arn:aws:iam::538653532257:role/BasicLambdaExecution
updateConfig:
	aws lambda update-function-configuration --function-name $(FUNCTION_NAME) \
		--region eu-west-1 \
		--logging-config="LogFormat=JSON,ApplicationLogLevel=DEBUG,SystemLogLevel=DEBUG,LogGroup=/aws/lambda/customlogGroup"
updateLambda:
	aws lambda update-function-code --function-name $(FUNCTION_NAME) \
		--s3-bucket=$(BUCKET_NAME) \
		--region eu-west-1 \
		--s3-key=$(JAR_FILE)

.PHONY: build s3copy createlambda create updateLambda update
