#!/bin/bash
mvn clean package
zip -r -j function.zip bootstrap target/aws-lambda-custom-runtime-java-1.0.jar