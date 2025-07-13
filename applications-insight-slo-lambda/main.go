package main

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
)

type Response struct {
	Message string `json:"message"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

func Handler(ctx context.Context, request events.APIGatewayProxyRequest) (events.APIGatewayProxyResponse, error) {
	mode := request.QueryStringParameters["mode"]

	if mode == "error" {
		errorMessage := ErrorResponse{
			Error: "This is a simulated error.",
		}
		body, _ := json.Marshal(errorMessage)
		return events.APIGatewayProxyResponse{
			StatusCode: 400,
			Body:       string(body),
			Headers: map[string]string{
				"Content-Type": "application/json",
			},
		}, nil
	}

	// Default to success
	response := Response{
		Message: "Hello, World! Everything is OK.",
	}
	body, err := json.Marshal(response)
	if err != nil {
		return events.APIGatewayProxyResponse{
			StatusCode: 500,
			Body:       fmt.Sprintf(`{"error":"%s"}`, err.Error()),
		}, nil
	}

	return events.APIGatewayProxyResponse{
		StatusCode: 200,
		Body:       string(body),
		Headers: map[string]string{
			"Content-Type": "application/json",
		},
	}, nil
}

func main() {
	// Start the Lambda handler
	lambda.Start(Handler)
}
