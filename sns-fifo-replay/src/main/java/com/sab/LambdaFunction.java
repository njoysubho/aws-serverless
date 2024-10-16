package com.sab;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.SNSEvent;

public class LambdaFunction implements RequestHandler<SNSEvent,String> {
    @Override
    public String handleRequest(SNSEvent snsEvent, Context context){
        return "Hello World - " + snsEvent.getRecords().get(0).getSNS().getMessage();
    }
}
