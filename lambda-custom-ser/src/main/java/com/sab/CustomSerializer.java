package com.sab;
import com.amazonaws.services.lambda.runtime.CustomPojoSerializer;

import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Type;
import java.lang.runtime.ObjectMethods;


public class CustomSerializer implements CustomPojoSerializer {

    private ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public <T> T fromJson(InputStream input, Type type){
        return null;
    }

    @Override
    public <T> T fromJson(String input, Type type){
        return null;
    }

    @Override
    public <T> void toJson(T value, OutputStream output, Type type){

    }
}
