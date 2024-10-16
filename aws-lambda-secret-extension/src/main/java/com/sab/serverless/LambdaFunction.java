package com.sab.serverless;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.ApplicationLoadBalancerRequestEvent;
import com.amazonaws.services.lambda.runtime.events.ApplicationLoadBalancerResponseEvent;
import com.sab.serverless.client.TmdbService;

import java.util.List;

public class LambdaFunction implements RequestHandler<ApplicationLoadBalancerRequestEvent, ApplicationLoadBalancerResponseEvent>{

    public LambdaFunction(){

    }

    @Override
    public ApplicationLoadBalancerResponseEvent handleRequest(ApplicationLoadBalancerRequestEvent event,Context context) {
        TmdbService tmdbService = new TmdbService();
        List<String> titles =  tmdbService.getMovies();
        ApplicationLoadBalancerResponseEvent response = new ApplicationLoadBalancerResponseEvent();
        response.setStatusCode(200);
        response.setBody(titles.toString());
        return response;
    }
}
