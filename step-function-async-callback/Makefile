# the name of the AWS Profile you want to use
AWS_PROFILE = "default"

GOOS=linux
GOARCH=arm64
CGO_ENABLED=0

.PHONY : all

all: build package deploy
# the first step is to build the binaries
build:
	echo "Running for function $(FUNCTION_NAME) with profile $(AWS_PROFILE)"
	mkdir -p bin
	GOOS=linux GOARCH=arm64 CGO_ENABLED=0 go build -v -o bin/bootstrap $(PWD)/app/functions/$(FUNCTION_NAME)/

package:
	echo "Packaging as zip"
	zip -rj bin/$(FUNCTION_NAME).zip bin/bootstrap
	rm bin/bootstrap

deploy:
	echo "Deploying on AWS"
	cd infra/$(FUNCTION_NAME) && cdk deploy --profile $(AWS_PROFILE)

destroy:
	echo "Deploying on AWS"
	cd infra/$(FUNCTION_NAME) && cdk destroy

