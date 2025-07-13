package com.example.handler;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.events.SQSEvent;
import com.example.model.Message;
import com.example.service.DynamoDbService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.Arrays;
import java.util.Collections;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class SnsSqusLambdaHandlerTest {

    @Mock
    private DynamoDbService dynamoDbService;

    @Mock
    private Context context;

    private SnsSqusLambdaHandler handler;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        handler = new SnsSqusLambdaHandler(dynamoDbService);
        objectMapper = new ObjectMapper();
    }

    @Test
    void testHandleRequest_WithDirectMessage() throws Exception {
        // Arrange
        Message testMessage = new Message("123", "Test Name");
        String messageJson = objectMapper.writeValueAsString(testMessage);

        SQSEvent.SQSMessage sqsMessage = new SQSEvent.SQSMessage();
        sqsMessage.setMessageId("msg-123");
        sqsMessage.setBody(messageJson);

        SQSEvent event = new SQSEvent();
        event.setRecords(Collections.singletonList(sqsMessage));

        // Act
        String result = handler.handleRequest(event, context);

        // Assert
        assertEquals("Processed: 1, Failed: 0", result);
        verify(dynamoDbService, times(1)).saveMessage(any(Message.class));
    }

    @Test
    void testHandleRequest_WithSNSWrappedMessage() throws Exception {
        // Arrange
        Message testMessage = new Message("456", "SNS Test Name");
        String messageJson = objectMapper.writeValueAsString(testMessage);
        
        String snsMessage = String.format("""
            {
                "Type": "Notification",
                "MessageId": "sns-msg-123",
                "TopicArn": "arn:aws:sns:us-east-1:123456789012:test-topic",
                "Message": "%s",
                "Timestamp": "2023-01-01T12:00:00.000Z"
            }
            """, messageJson.replace("\"", "\\\""));

        SQSEvent.SQSMessage sqsMessage = new SQSEvent.SQSMessage();
        sqsMessage.setMessageId("msg-456");
        sqsMessage.setBody(snsMessage);

        SQSEvent event = new SQSEvent();
        event.setRecords(Collections.singletonList(sqsMessage));

        // Act
        String result = handler.handleRequest(event, context);

        // Assert
        assertEquals("Processed: 1, Failed: 0", result);
        verify(dynamoDbService, times(1)).saveMessage(any(Message.class));
    }

    @Test
    void testHandleRequest_WithMultipleMessages() throws Exception {
        // Arrange
        Message message1 = new Message("123", "Name 1");
        Message message2 = new Message("456", "Name 2");
        
        String messageJson1 = objectMapper.writeValueAsString(message1);
        String messageJson2 = objectMapper.writeValueAsString(message2);

        SQSEvent.SQSMessage sqsMessage1 = new SQSEvent.SQSMessage();
        sqsMessage1.setMessageId("msg-123");
        sqsMessage1.setBody(messageJson1);

        SQSEvent.SQSMessage sqsMessage2 = new SQSEvent.SQSMessage();
        sqsMessage2.setMessageId("msg-456");
        sqsMessage2.setBody(messageJson2);

        SQSEvent event = new SQSEvent();
        event.setRecords(Arrays.asList(sqsMessage1, sqsMessage2));

        // Act
        String result = handler.handleRequest(event, context);

        // Assert
        assertEquals("Processed: 2, Failed: 0", result);
        verify(dynamoDbService, times(2)).saveMessage(any(Message.class));
    }

    @Test
    void testHandleRequest_WithInvalidMessage() throws Exception {
        // Arrange
        String invalidJson = "{\"invalid\": \"message\"}";

        SQSEvent.SQSMessage sqsMessage = new SQSEvent.SQSMessage();
        sqsMessage.setMessageId("msg-invalid");
        sqsMessage.setBody(invalidJson);

        SQSEvent event = new SQSEvent();
        event.setRecords(Collections.singletonList(sqsMessage));

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            handler.handleRequest(event, context);
        });

        assertTrue(exception.getMessage().contains("Some messages failed to process"));
        verify(dynamoDbService, never()).saveMessage(any(Message.class));
    }

    @Test
    void testHandleRequest_WithDynamoDbException() throws Exception {
        // Arrange
        Message testMessage = new Message("123", "Test Name");
        String messageJson = objectMapper.writeValueAsString(testMessage);

        SQSEvent.SQSMessage sqsMessage = new SQSEvent.SQSMessage();
        sqsMessage.setMessageId("msg-123");
        sqsMessage.setBody(messageJson);

        SQSEvent event = new SQSEvent();
        event.setRecords(Collections.singletonList(sqsMessage));

        doThrow(new RuntimeException("DynamoDB error")).when(dynamoDbService).saveMessage(any(Message.class));

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            handler.handleRequest(event, context);
        });

        assertTrue(exception.getMessage().contains("Some messages failed to process"));
        verify(dynamoDbService, times(1)).saveMessage(any(Message.class));
    }

    @Test
    void testHandleRequest_WithMissingIdField() throws Exception {
        // Arrange
        String invalidMessage = "{\"name\": \"Test Name\"}"; // Missing id field

        SQSEvent.SQSMessage sqsMessage = new SQSEvent.SQSMessage();
        sqsMessage.setMessageId("msg-123");
        sqsMessage.setBody(invalidMessage);

        SQSEvent event = new SQSEvent();
        event.setRecords(Collections.singletonList(sqsMessage));

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            handler.handleRequest(event, context);
        });

        assertTrue(exception.getMessage().contains("Some messages failed to process"));
        verify(dynamoDbService, never()).saveMessage(any(Message.class));
    }

    @Test
    void testHandleRequest_WithMissingNameField() throws Exception {
        // Arrange
        String invalidMessage = "{\"id\": \"123\"}"; // Missing name field

        SQSEvent.SQSMessage sqsMessage = new SQSEvent.SQSMessage();
        sqsMessage.setMessageId("msg-123");
        sqsMessage.setBody(invalidMessage);

        SQSEvent event = new SQSEvent();
        event.setRecords(Collections.singletonList(sqsMessage));

        // Act & Assert
        RuntimeException exception = assertThrows(RuntimeException.class, () -> {
            handler.handleRequest(event, context);
        });

        assertTrue(exception.getMessage().contains("Some messages failed to process"));
        verify(dynamoDbService, never()).saveMessage(any(Message.class));
    }
}