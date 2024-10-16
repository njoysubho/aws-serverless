package main

import (
	"context"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/njoysubho/step-function-async-callback/app/internal/logger"
)

type Approval struct {
	OrderId  string   `json:"orderId"`
	Workflow WorkFlow `json:"workflow"`
}

type WorkFlow struct {
	Tasks []Task `json:"tasks"`
}

type Task struct {
	OrderId string `json:"orderId"`
	Task    string `json:"task"`
}

func Handler(ctx context.Context, event Approval) error {
	logger.Infof("Received msg", event)
	return nil
}
func main() {
	logger.Init()
	lambda.Start(Handler)
}
