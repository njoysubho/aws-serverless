package com.example.service;

import com.example.model.Message;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedClient;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbTable;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Service class to handle DynamoDB operations
 */
public class DynamoDbService {
    
    private static final Logger logger = LoggerFactory.getLogger(DynamoDbService.class);
    private final DynamoDbTable<Message> messageTable;
    
    public DynamoDbService() {
        this(System.getenv("TABLE_NAME"));
    }
    
    public DynamoDbService(String tableName) {
        if (tableName == null || tableName.trim().isEmpty()) {
            throw new IllegalArgumentException("TABLE_NAME environment variable must be set");
        }
        
        DynamoDbClient dynamoDbClient = DynamoDbClient.builder()
                .region(Region.of(System.getenv().getOrDefault("AWS_REGION", "us-east-1")))
                .build();
        
        DynamoDbEnhancedClient enhancedClient = DynamoDbEnhancedClient.builder()
                .dynamoDbClient(dynamoDbClient)
                .build();
        
        this.messageTable = enhancedClient.table(tableName, TableSchema.fromBean(Message.class));
        
        logger.info("DynamoDbService initialized with table: {}", tableName);
    }
    
    /**
     * Save a message to DynamoDB
     * @param message The message to save
     */
    public void saveMessage(Message message) {
        try {
            messageTable.putItem(message);
            logger.info("Successfully saved message with id: {}", message.getId());
        } catch (Exception e) {
            logger.error("Failed to save message with id: {}", message.getId(), e);
            throw new RuntimeException("Failed to save message to DynamoDB", e);
        }
    }
}