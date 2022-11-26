package com.sab.runtime;

import com.amazonaws.lambda.thirdparty.com.fasterxml.jackson.databind.ObjectMapper;
import com.amazonaws.lambda.thirdparty.com.fasterxml.jackson.databind.SerializationFeature;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.api.client.ReservedRuntimeEnvironmentVariables;
import com.amazonaws.services.lambda.runtime.api.client.api.LambdaContext;
import com.amazonaws.services.lambda.runtime.api.client.runtimeapi.InvocationRequest;
import com.amazonaws.services.lambda.runtime.api.client.runtimeapi.LambdaRuntimeClient;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyResponseEvent;
import com.amazonaws.services.lambda.runtime.serialization.factories.JacksonFactory;

import java.io.*;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.Optional;

public class AwsRuntime{
    private static final JacksonFactory JACKSON_FACTORY = JacksonFactory.getInstance();
    private static  final ObjectMapper MAPPER = new ObjectMapper();
    public static void main(String[] args){
       MAPPER.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);
        try {
            startRuntime();
        } catch (Throwable t) {
            throw new Error(t);
        }
    }

    private static void startRuntime() throws IOException{
        Context context = null;
        boolean exit = false;
        LambdaRuntimeClient lambdaRuntimeClient = null;
        while (!exit) {
            try {
                //Retrieve Settings
                String handlerName = getEnvOrExit(ReservedRuntimeEnvironmentVariables.HANDLER);
                String hostNamePort = getEnvOrExit(ReservedRuntimeEnvironmentVariables.AWS_LAMBDA_RUNTIME_API);
                lambdaRuntimeClient = new LambdaRuntimeClient(hostNamePort);
                // initialize
                //load handler
                var handler = initHandler(handlerName);
                //Get event data
                var invocationRequest = lambdaRuntimeClient.waitForNextInvocation();
                System.out.println(MAPPER.writeValueAsString(invocationRequest));
                // create lambda execution context
                context = new LambdaContext(LambdaEnvironment.MEMORY_LIMIT,
                        invocationRequest.getDeadlineTimeInMs(),
                        invocationRequest.getId(),
                        LambdaEnvironment.LOG_GROUP_NAME,
                        LambdaEnvironment.LOG_STREAM_NAME,
                        LambdaEnvironment.FUNCTION_NAME,
                        null,
                        LambdaEnvironment.FUNCTION_VERSION,
                        invocationRequest.getInvokedFunctionArn(),
                        null);
                //invoke handler
                Object output = invokeHandler(context, invocationRequest, handler);
                // send response back
                ByteArrayOutputStream outputStream = getByteArrayOutputStream(handler.method(), output);
                lambdaRuntimeClient.postInvocationResponse(context.getAwsRequestId(), outputStream.toByteArray());

            } catch (Throwable th) {
                th.printStackTrace();
                System.err.println("Error occured executing lambda with context " + context);
                lambdaRuntimeClient.postInvocationError(context.getAwsRequestId(),
                        th.toString().getBytes(StandardCharsets.UTF_8), "Runtime.Unknown"
                );
                exit = true;
            }
        }
    }

    private static Object invokeHandler(Context context, InvocationRequest invocationRequest, Handler handler) throws InstantiationException, IllegalAccessException, InvocationTargetException, NoSuchMethodException, IOException{
        var handlerMethod = handler.method();
        var handlerObject = handler.clazz().getDeclaredConstructor().newInstance();
        var payload = findPayload(invocationRequest.getContentAsStream(), handlerMethod.getParameterTypes());
        var output = handlerMethod.invoke(handlerObject, payload, context);
        return output;
    }

    private static ByteArrayOutputStream getByteArrayOutputStream(Method handlerMethod, Object output){
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        toJson(output, outputStream, handlerMethod.getReturnType());
        return outputStream;
    }

    private static void toJson(Object output, ByteArrayOutputStream outputStream, Class returnType){
        var responseSerializer = JACKSON_FACTORY.getSerializer(returnType);
        if (returnType.isAssignableFrom(APIGatewayProxyResponseEvent.class)) {
            var apiGatewayResponse = (APIGatewayProxyResponseEvent) output;
            responseSerializer.toJson(apiGatewayResponse, outputStream);
        } else {
            responseSerializer.toJson(output, outputStream);
        }
    }

    private static Object findPayload(InputStream contentAsStream, Class<?>[] parameterTypes) throws IOException{
        var firstClass = parameterTypes[0];
        var serializer = JACKSON_FACTORY.getSerializer(firstClass);
        return serializer.fromJson(contentAsStream);
    }

    private static byte[] convertToBytes(Object object) throws IOException{
        try (ByteArrayOutputStream bos = new ByteArrayOutputStream()) {
            ObjectOutputStream out = new ObjectOutputStream(bos);
            out.writeObject(object);
            return bos.toByteArray();
        }
    }

    private static Handler initHandler(String handler) throws ClassNotFoundException, NoSuchMethodException{
        var mayBeHandlerClass = parseHandlerClass(handler);
        Method method = null;
        Class handlerClass = null;
        if (mayBeHandlerClass.isPresent()) {
            handlerClass = mayBeHandlerClass.get();
            method = handlerClass.getMethod("handleRequest", APIGatewayProxyRequestEvent.class, Context.class);
        }
        return new Handler(handlerClass, method);
    }

    public static String getEnvOrExit(String envVariableName){
        String value = System.getenv(envVariableName);
        if (value == null) {
            System.err.println("Could not get environment variable " + envVariableName);
            System.exit(-1);
        }
        return value;
    }

    protected static Optional<Class> parseHandlerClass(String handler) throws ClassNotFoundException{
        String[] arr = handler.split("::");
        if (arr.length > 0) {
            return Optional.of(Class.forName(arr[0]));
        }
        return Optional.empty();
    }
}
