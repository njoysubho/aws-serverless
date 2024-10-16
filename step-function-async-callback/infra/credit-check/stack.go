package main

import (
	"github.com/aws/aws-cdk-go/awscdk/v2"
	"github.com/aws/aws-cdk-go/awscdk/v2/awsiam"
	"github.com/aws/aws-cdk-go/awscdk/v2/awslambda"
	"github.com/aws/aws-cdk-go/awscdk/v2/awslambdaeventsources"
	"github.com/aws/aws-cdk-go/awscdk/v2/awssns"
	"github.com/aws/aws-cdk-go/awscdk/v2/awssnssubscriptions"
	"github.com/aws/aws-cdk-go/awscdk/v2/awssqs"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/constructs-go/constructs/v10"
)

func CreditCheckStack(scope constructs.Construct, stackName string) awscdk.Stack {
	stack := awscdk.NewStack(scope, &stackName, &awscdk.StackProps{
		Env: &awscdk.Environment{
			Account: nil,
			Region:  aws.String("us-west-2"),
		},
	})
	account := stack.Account()
	// task topic
	taskTopicArn := "arn:aws:sns:us-west-2:" + *account + ":task"
	//lambda
	lambda := createCreditCheckLambda(stack)
	// queue
	queue := createQueue(stack)
	// SNS -> SQS Subscription with filter
	snsSub := awssnssubscriptions.NewSqsSubscription(queue, &awssnssubscriptions.SqsSubscriptionProps{
		FilterPolicy: &map[string]awssns.SubscriptionFilter{
			"Task": awssns.SubscriptionFilter_StringFilter(&awssns.StringConditions{
				MatchPrefixes: &[]*string{aws.String("credit-check")},
			}),
		},
	})
	taskTopic := awssns.Topic_FromTopicArn(stack, aws.String("task-topic"), aws.String(taskTopicArn))
	taskTopic.AddSubscription(snsSub)
	// event source mapping
	sqsEventSource := awslambdaeventsources.NewSqsEventSource(queue, nil)

	lambda.AddEventSource(sqsEventSource)
	return stack
}
func createQueue(stack awscdk.Stack) awssqs.Queue {
	return awssqs.NewQueue(stack, aws.String("credit-check-task-queue"), &awssqs.QueueProps{
		QueueName: aws.String("credit-check-task-queue"),
	})
}
func createCreditCheckLambda(stack awscdk.Stack) awslambda.Function {
	lambdaRole := "arn:aws:iam::" + *stack.Account() + ":role/BasicLambdaExecution"

	//Lambda
	lambda := awslambda.NewFunction(stack, aws.String("credit-check-lambda"), &awslambda.FunctionProps{
		Description:  aws.String("Check credit score"),
		FunctionName: aws.String("credit-check-lambda"),

		MemorySize:   aws.Float64(128),
		Code:         awslambda.Code_FromAsset(aws.String("../../bin/credit-check.zip"), nil),
		Handler:      aws.String("bootstrap"),
		Role:         awsiam.Role_FromRoleArn(stack, aws.String("lambdaExecutionRole"), aws.String(lambdaRole), nil),
		Runtime:      awslambda.Runtime_PROVIDED_AL2(),
		Architecture: awslambda.Architecture_ARM_64(),
	})
	return lambda
}

func main() {
	app := awscdk.NewApp(nil)
	CreditCheckStack(app, "CreditCheckStack")
	app.Synth(nil)
}
