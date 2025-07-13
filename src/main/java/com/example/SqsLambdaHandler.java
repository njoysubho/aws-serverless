package com.example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;

/**
 * Lambda function handler for processing SQS messages.
 * This handler processes each message in the SQS event and demonstrates
 * common patterns for SQS message processing.
 */
public class SqsLambdaHandler implements RequestHandler<SQSEvent, String> {

    private static final Logger logger = LoggerFactory.getLogger(SqsLambdaHandler.class);
    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public String handleRequest(SQSEvent event, Context context) {
        logger.info("Received SQS event with {} records", event.getRecords().size());
        
        int processedCount = 0;
        int errorCount = 0;

        // Process each message in the SQS event
        for (SQSEvent.SQSMessage message : event.getRecords()) {
            try {
                processMessage(message, context);
                processedCount++;
                logger.info("Successfully processed message: {}", message.getMessageId());
            } catch (Exception e) {
                errorCount++;
                logger.error("Error processing message {}: {}", message.getMessageId(), e.getMessage(), e);
                
                // In a real application, you might want to:
                // 1. Send failed messages to a DLQ (Dead Letter Queue)
                // 2. Implement retry logic
                // 3. Send alerts/notifications
                handleProcessingError(message, e, context);
            }
        }

        String result = String.format("Processed %d messages successfully, %d errors", 
                                    processedCount, errorCount);
        logger.info("Batch processing completed: {}", result);
        
        return result;
    }

    /**
     * Process an individual SQS message.
     * Override this method to implement your specific business logic.
     */
    private void processMessage(SQSEvent.SQSMessage message, Context context) {
        logger.info("Processing message from queue: {}", message.getEventSourceArn());
        logger.info("Message ID: {}", message.getMessageId());
        logger.info("Receipt Handle: {}", message.getReceiptHandle());
        
        // Extract message body
        String messageBody = message.getBody();
        logger.info("Message body: {}", messageBody);
        
        // Process message attributes if present
        if (message.getMessageAttributes() != null && !message.getMessageAttributes().isEmpty()) {
            logger.info("Message has {} attributes", message.getMessageAttributes().size());
            message.getMessageAttributes().forEach((key, value) -> {
                logger.info("Attribute {}: {} (type: {})", key, value.getStringValue(), value.getDataType());
            });
        }

        // Example: Parse JSON message body
        try {
            if (isJsonMessage(messageBody)) {
                processJsonMessage(messageBody);
            } else {
                processPlainTextMessage(messageBody);
            }
        } catch (Exception e) {
            logger.error("Error parsing message body: {}", e.getMessage());
            throw new MessageProcessingException("Failed to parse message body", e);
        }

        // Simulate some processing time
        try {
            Thread.sleep(100);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new MessageProcessingException("Message processing interrupted", e);
        }

        logger.info("Message processing completed for message: {}", message.getMessageId());
    }

    /**
     * Check if the message body is JSON format
     */
    private boolean isJsonMessage(String messageBody) {
        return messageBody.trim().startsWith("{") || messageBody.trim().startsWith("[");
    }

    /**
     * Process JSON formatted message
     */
    private void processJsonMessage(String messageBody) {
        try {
            // Example: Parse as generic JSON object
            Object jsonObject = objectMapper.readValue(messageBody, Object.class);
            logger.info("Parsed JSON message: {}", jsonObject);
            
            // Here you would implement your specific JSON processing logic
            // For example, you might deserialize to a specific POJO:
            // MyMessageType message = objectMapper.readValue(messageBody, MyMessageType.class);
            
        } catch (Exception e) {
            logger.error("Failed to parse JSON message: {}", e.getMessage());
            throw new MessageProcessingException("Invalid JSON format", e);
        }
    }

    /**
     * Process plain text message
     */
    private void processPlainTextMessage(String messageBody) {
        logger.info("Processing plain text message: {}", messageBody);
        
        // Implement your plain text processing logic here
        // For example: email processing, log parsing, etc.
    }

    /**
     * Handle processing errors
     */
    private void handleProcessingError(SQSEvent.SQSMessage message, Exception error, Context context) {
        logger.error("Handling processing error for message: {}", message.getMessageId());
        
        // Example error handling strategies:
        // 1. Log detailed error information
        logger.error("Error details - Message: {}, Queue: {}, Error: {}", 
                    message.getMessageId(), 
                    message.getEventSourceArn(), 
                    error.getMessage());
        
        // 2. Send to monitoring/alerting system
        // sendErrorAlert(message, error, context);
        
        // 3. Store error details for later analysis
        // storeErrorDetails(message, error, context);
        
        // Note: If you throw an exception here, the message will be retried
        // or sent to a DLQ based on your SQS configuration
    }

    /**
     * Custom exception for message processing errors
     */
    public static class MessageProcessingException extends RuntimeException {
        public MessageProcessingException(String message) {
            super(message);
        }
        
        public MessageProcessingException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}