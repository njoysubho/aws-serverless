package com.sab.serverless;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.LambdaLogger;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.logging.LogLevel;

public class LambdaHandler implements RequestHandler<String, String>{
    public String handleRequest(String input, Context context){
        LambdaLogger lambdaLogger = context.getLogger();

        lambdaLogger.log("This is an info log ", LogLevel.INFO);
        lambdaLogger.log("This is a debug log", LogLevel.DEBUG);
        return "Hello World - " + input;
    }
}
