use lambda_http::{Body, Error, Request, Response, run, service_fn, tracing};

/// This is the main body for the function.
/// Write your code inside it.
/// There are some code example in the following URLs:
/// - https://github.com/awslabs/aws-lambda-rust-runtime/tree/main/examples
async fn function_handler(event: Request) -> Result<Response<Body>, Error> {
    // Extract some useful information from the request
    let body = event.body();
    if body.is_empty() {
        let error_resp = Response::builder()
            .status(400)
            .body("Request should have a body".into())
            .map_err(Box::new)?;
        return  Ok(error_resp);
    }
    let message = "Hello this is an AWS Lambda HTTP request";

    // Return something that implements IntoResponse.
    // It will be serialized to the right response event automatically by the runtime
    let resp = Response::builder()
        .status(200)
        .body(message.into())
        .map_err(Box::new)?;
    Ok(resp)
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing::init_default_subscriber();

    run(service_fn(function_handler)).await
}
