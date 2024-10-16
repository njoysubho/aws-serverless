package com.sab.serverless.secret;

import lombok.extern.log4j.Log4j2;
import okhttp3.Call;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

import java.io.IOException;

@Log4j2
public class SecretManager{

    public String getSecret(String secretId){
        String port = System.getenv("PARAMETERS_SECRETS_EXTENSION_HTTP_PORT");
        String AWS_SESSION_TOKEN = System.getenv("AWS_SESSION_TOKEN");
        OkHttpClient client = new OkHttpClient();
        Request request = new Request.Builder()
                .url("http://localhost:2773/secretsmanager/get?secretId=" + secretId)
                .get()
                .addHeader("X-Aws-Parameters-Secrets-Token", AWS_SESSION_TOKEN)
                .build();
        Call call = client.newCall(request);
        Response response = null;
        try {
            response = call.execute();
            String secret = response.body().string();
            System.out.println("Response: " + secret);
            return secret;
        } catch (IOException e) {
            log.error("Error getting secret: " + e.getMessage());
        }
        return null;
    }
}
