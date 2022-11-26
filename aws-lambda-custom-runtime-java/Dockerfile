FROM amazoncorretto:19 as build

RUN yum -y update
RUN yum install -y  maven zip
COPY . .

RUN mvn clean package

RUN jdeps -q \
    --ignore-missing-deps \
    --multi-release 19 \
    --print-module-deps \
    target/aws-lambda-custom-runtime-java-1.0.jar > jre-deps.info

RUN cat jre-deps.info
RUN ls /usr/lib/jvm
RUN jlink --verbose \
    --module-path "%JAVA_HOME%\jmods" \
    --compress 2 \
    --strip-java-debug-attributes \
    --no-header-files \
    --no-man-pages \
    --output /jre19-slim \
    --add-modules $(cat jre-deps.info)

RUN cp target/aws-lambda-custom-runtime-java-1.0.jar aws-lambda-custom-runtime-java-1.0.jar

RUN zip -r  function.zip \
    bootstrap \
     aws-lambda-custom-runtime-java-1.0.jar \
    /jre19-slim

FROM scratch

COPY --from=build /function.zip function.zip