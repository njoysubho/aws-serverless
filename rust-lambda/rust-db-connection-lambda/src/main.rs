use diesel::RunQueryDsl;
use lambda_http::{run, service_fn, tracing, Body, Error, Request, RequestExt, Response};
use rust_db_connection_lambda::{create_connection, create_post};
use crate::schema::posts;

mod models;
mod schema;
async fn function_handler(event: Request) -> Result<Response<Body>, Error> {

    let db_conn = &mut create_connection();

    let new_post = create_post(db_conn, "Hello", "This is a post");

    let body = event.body();
    if body.is_empty() {
        let error_resp = Response::builder()
            .status(400)
            .body("Request should have a body".into())
            .map_err(Box::new)?;
        return Ok(error_resp);
    }


    Ok(resp)
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    tracing::init_default_subscriber();

    run(service_fn(function_handler)).await
}
