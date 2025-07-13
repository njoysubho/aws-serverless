package com.example.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;

/**
 * Message model representing the data structure with id and name fields
 */
@DynamoDbBean
public class Message {
    
    private String id;
    private String name;

    public Message() {
        // Default constructor required for DynamoDB Enhanced Client
    }

    public Message(String id, String name) {
        this.id = id;
        this.name = name;
    }

    @DynamoDbPartitionKey
    @JsonProperty("id")
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    @JsonProperty("name")
    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    @Override
    public String toString() {
        return "Message{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                '}';
    }
}