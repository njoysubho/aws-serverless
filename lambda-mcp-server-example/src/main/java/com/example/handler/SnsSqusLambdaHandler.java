package com.example.handler;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.example.model.Message;
import com.example.service.DynamoDbService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Lambda handler for processing SQS messages triggered by SNS fanout
 */
public class SnsSqusLambdaHandler implements RequestHandler<SQSEvent, String> {
    
    private static final Logger logger = LoggerFactory.getLogger(SnsSqusLambdaHandler.class);
    private final DynamoDbService dynamoDbService;
    private final ObjectMapper objectMapper;
    
    public SnsSqusLambdaHandler() {
        this.dynamoDbService = new DynamoDbService();
        this.objectMapper = new ObjectMapper();
    }
    
    // Constructor for testing
    public SnsSqusLambdaHandler(DynamoDbService dynamoDbService) {
        this.dynamoDbService = dynamoDbService;
        this.objectMapper = new ObjectMapper();
    }
    
    @Override
    public String handleRequest(SQSEvent event, Context context) {
        logger.info("Processing SQS event with {} records", event.getRecords().size());
        
        int processedCount = 0;
        int failedCount = 0;
        
        for (SQSEvent.SQSMessage sqsMessage : event.getRecords()) {
            try {
                processMessage(sqsMessage);
                processedCount++;
            } catch (Exception e) {
                logger.error("Failed to process message with ID: {}", sqsMessage.getMessageId(), e);
                failedCount++;
            }
        }
        
        String result = String.format("Processed: %d, Failed: %d", processedCount, failedCount);
        logger.info("Processing completed. {}", result);
        
        if (failedCount > 0) {
            throw new RuntimeException("Some messages failed to process. " + result);
        }
        
        return result;
    }
    
    private void processMessage(SQSEvent.SQSMessage sqsMessage) throws Exception {
        logger.info("Processing message ID: {}", sqsMessage.getMessageId());
        
        String messageBody = sqsMessage.getBody();
        logger.debug("Message body: {}", messageBody);
        
        // Parse SNS message if it's wrapped in SNS format
        String actualMessage = extractMessageFromSns(messageBody);
        
        // Parse the actual message content
        Message message = objectMapper.readValue(actualMessage, Message.class);
        
        // Validate message
        validateMessage(message);
        
        // Save to DynamoDB
        dynamoDbService.saveMessage(message);
        
        logger.info("Successfully processed message with id: {} and name: {}", 
                   message.getId(), message.getName());
    }
    
    private String extractMessageFromSns(String messageBody) throws Exception {
        try {
            // Try to parse as SNS message first
            var snsMessage = objectMapper.readTree(messageBody);
            
            if (snsMessage.has("Message")) {
                // This is an SNS message, extract the actual message
                String actualMessage = snsMessage.get("Message").asText();
                logger.debug("Extracted message from SNS wrapper: {}", actualMessage);
                return actualMessage;
            } else {
                // This might be a direct SQS message
                return messageBody;
            }
        } catch (Exception e) {
            logger.warn("Failed to parse as SNS message, treating as direct message: {}", e.getMessage());
            return messageBody;
        }
    }
    
    private void validateMessage(Message message) {
        if (message.getId() == null || message.getId().trim().isEmpty()) {
            throw new IllegalArgumentException("Message ID cannot be null or empty");
        }
        
        if (message.getName() == null || message.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("Message name cannot be null or empty");
        }
        
        logger.debug("Message validation passed for id: {}", message.getId());
    }
}