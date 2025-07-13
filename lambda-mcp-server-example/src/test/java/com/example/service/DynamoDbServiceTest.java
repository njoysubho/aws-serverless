package com.example.service;

import com.example.model.Message;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DynamoDbServiceTest {

    @Test
    void testConstructorWithNullTableName() {
        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            new DynamoDbService(null);
        });
        
        assertEquals("TABLE_NAME environment variable must be set", exception.getMessage());
    }

    @Test
    void testConstructorWithEmptyTableName() {
        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            new DynamoDbService("");
        });
        
        assertEquals("TABLE_NAME environment variable must be set", exception.getMessage());
    }

    @Test
    void testConstructorWithBlankTableName() {
        // Act & Assert
        IllegalArgumentException exception = assertThrows(IllegalArgumentException.class, () -> {
            new DynamoDbService("   ");
        });
        
        assertEquals("TABLE_NAME environment variable must be set", exception.getMessage());
    }

    // Note: Integration tests for actual DynamoDB operations would require
    // either a real DynamoDB table (expensive) or DynamoDB Local/TestContainers
    // For unit testing the save functionality, you would typically mock the
    // DynamoDbTable or use dependency injection to provide a mock
}