terraform {
  required_providers {
            aws = {
                source = "hashicorp/aws"
                version = ""
            }
        }
  backend "s3" {
    bucket = "terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
    region = "us-east-1"
}

// create a lambda with sns
 resource "aws_lambda_function" "sns-fifo-replay-lambda" {
   function_name = "sns-fifo-replay-lambda"
   role          = "${aws_iam_role.sns-fifo-replay.arn}"
 }

resource "aws_iam_role" "lambda-exec-role" {
    name = "sns-fifo-replay"
    assume_role_policy = <<EOF
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Action": "sts:AssumeRole",
        "Principal": {
            "Service": "lambda.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
        }
    ]
    }
EOF
}

resource "aws_iam_role_policy" "sns-fifo-replay" {
    name = "sns-fifo-replay"
    role = aws_iam_role.sns-fifo-replay.id

    policy = <<EOF
    {
    "Version": "2012-10-17",
    "Statement": [
        {
        "Action": [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:PutLogEvents"
        ],
        "Effect": "Allow",
        "Resource": "arn:aws:logs:*:*:*"
        },
        {
        "Action": [
            "sns:Publish"
        ],
        "Effect": "Allow",
        "Resource": "*"
        }
    ]
    }
EOF
}

resource "aws_sns_topic" "sns-fifo-replay" {
    name = "sns-fifo-replay"
    fifo_topic = true
    content_based_deduplication = true
    message_retention_policy {
        max_message_size = 1024
        retention_period = 86400
    }
}

resource "aws_lambda_permission" "sns-fifo-replay" {
    statement_id  = "AllowExecutionFromSNS"
    action        = "lambda:InvokeFunction"
    function_name = aws_lambda_function.sns-fifo-replay.function_name
    principal     = "sns.amazonaws.com"
    source_arn    = aws_sns_topic.sns-fifo-replay.arn
}
