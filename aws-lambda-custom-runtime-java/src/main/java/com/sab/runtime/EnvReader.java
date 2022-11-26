package com.sab.runtime;

import java.util.Map;

public class EnvReader {

    public Map<String, String> getEnv() {
        return System.getenv();
    }

    public String getEnv(String envVariableName) {
        return System.getenv(envVariableName);
    }

    public String getEnvOrDefault(String envVariableName, String defaultVal) {
        String val = getEnv(envVariableName);
        return val == null ? defaultVal : val;
    }

}
