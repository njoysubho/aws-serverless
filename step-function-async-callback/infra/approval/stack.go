package main

import (
	"github.com/aws/aws-cdk-go/awscdk/v2"
	"github.com/aws/aws-cdk-go/awscdk/v2/awsiam"
	"github.com/aws/aws-cdk-go/awscdk/v2/awslambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/constructs-go/constructs/v10"
)

func ApprovalStack(scope constructs.Construct, stackName string) awscdk.Stack {
	stack := awscdk.NewStack(scope, &stackName, &awscdk.StackProps{
		Env: &awscdk.Environment{
			Account: nil,
			Region:  aws.String("us-west-2"),
		},
	})

	//lambda
	approvalLambda(stack)
	return stack
}

func approvalLambda(stack awscdk.Stack) awslambda.Function {
	lambdaRole := "arn:aws:iam::" + *stack.Account() + ":role/BasicLambdaExecution"

	//Lambda
	lambda := awslambda.NewFunction(stack, aws.String("approval-lambda"), &awslambda.FunctionProps{
		Description:  aws.String("Approval"),
		FunctionName: aws.String("approval-lambda"),

		MemorySize:   aws.Float64(128),
		Code:         awslambda.Code_FromAsset(aws.String("../../bin/approval.zip"), nil),
		Handler:      aws.String("bootstrap"),
		Role:         awsiam.Role_FromRoleArn(stack, aws.String("lambdaExecutionRole"), aws.String(lambdaRole), nil),
		Runtime:      awslambda.Runtime_PROVIDED_AL2(),
		Architecture: awslambda.Architecture_ARM_64(),
	})
	return lambda
}

func main() {
	app := awscdk.NewApp(nil)
	ApprovalStack(app, "ApprovalStack")
	app.Synth(nil)
}
