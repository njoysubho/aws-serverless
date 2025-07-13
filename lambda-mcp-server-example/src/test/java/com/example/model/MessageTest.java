package com.example.model;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class MessageTest {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Test
    void testMessageCreation() {
        // Arrange & Act
        Message message = new Message("123", "Test Name");

        // Assert
        assertEquals("123", message.getId());
        assertEquals("Test Name", message.getName());
    }

    @Test
    void testDefaultConstructor() {
        // Arrange & Act
        Message message = new Message();

        // Assert
        assertNull(message.getId());
        assertNull(message.getName());
    }

    @Test
    void testSetters() {
        // Arrange
        Message message = new Message();

        // Act
        message.setId("456");
        message.setName("Another Name");

        // Assert
        assertEquals("456", message.getId());
        assertEquals("Another Name", message.getName());
    }

    @Test
    void testJsonSerialization() throws Exception {
        // Arrange
        Message message = new Message("789", "JSON Test");

        // Act
        String json = objectMapper.writeValueAsString(message);

        // Assert
        assertTrue(json.contains("\"id\":\"789\""));
        assertTrue(json.contains("\"name\":\"JSON Test\""));
    }

    @Test
    void testJsonDeserialization() throws Exception {
        // Arrange
        String json = "{\"id\":\"101\",\"name\":\"Deserialized Name\"}";

        // Act
        Message message = objectMapper.readValue(json, Message.class);

        // Assert
        assertEquals("101", message.getId());
        assertEquals("Deserialized Name", message.getName());
    }

    @Test
    void testToString() {
        // Arrange
        Message message = new Message("999", "ToString Test");

        // Act
        String result = message.toString();

        // Assert
        assertTrue(result.contains("id='999'"));
        assertTrue(result.contains("name='ToString Test'"));
    }
}