package com.sab.serverless.secret;

import lombok.Data;

@Data
public class Secret{
    @JsonProperty("SecretString")
    private String secretString;
}
