package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/sfn"
	"github.com/njoysubho/step-function-async-callback/app/internal/logger"
)

func Handler(ctx context.Context, event events.SQSEvent) error {
	logger.Infof("Received msg %s", event.Records)
	cfg, err := config.LoadDefaultConfig(context.TODO(),
		config.WithRegion("us-west-2"),
	)
	if err != nil {
		logger.Errorf("error creating step function client %s", err.Error())
		return err
	}

	sfnClient := sfn.NewFromConfig(cfg)

	msgs := event.Records
	for _, msg := range msgs {
		msgBody := msg.Body
		logger.Infof("Processing msg %s", msg.Body)
		snsEvent := &events.SNSEntity{}
		err := json.Unmarshal([]byte(msgBody), snsEvent)
		if err != nil {
			logger.Errorf("error sending task success signal to sfn %s", err.Error())
			return err
		}
		logger.Infof("token is %s", snsEvent.MessageAttributes["TaskToken"])
		taskTokenAttribute := snsEvent.MessageAttributes["TaskToken"].(map[string]interface{})
		taskTokenValue := fmt.Sprintf("%v", taskTokenAttribute["Value"])
		logger.Infof("Token is %s", taskTokenValue)
		// Do some business logic check
		logger.Infof("Successfully completed income check")
		_, err = sfnClient.SendTaskSuccess(ctx, &sfn.SendTaskSuccessInput{
			Output:    aws.String("{\"result\":\"Income Check Done\"}"),
			TaskToken: &taskTokenValue,
		})
		if err != nil {
			logger.Errorf("error sending task success signal to sfn %s", err.Error())
			return err
		}

	}
	return nil
}
func main() {
	logger.Init()
	logger.Infof("Starting Lambda Income Check")
	lambda.Start(Handler)
}
