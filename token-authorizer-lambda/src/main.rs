use lambda_runtime::{service_fn, Context, Error};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use jsonwebtoken::{decode, Algorithm, DecodingKey, Validation};
use reqwest::Client;
use base64::{Engine as _, alphabet, engine::{self, general_purpose}};

#[derive(Deserialize)]
#[serde(rename_all = "camelCase")]
struct AuthEvent {
    authorization_token: String,
    method_arn: String,
}

#[derive(Serialize)]
struct PolicyDocument {
    Version: String,
    Statement: Vec<Statement>,
}

#[derive(Serialize)]
struct Statement {
    Action: String,
    Effect: String,
    Resource: String,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct AuthResponse {
    principal_id: String,
    policy_document: PolicyDocument,
}

async fn fetch_jwks(jwks_url: &str) -> Result<Value, Error> {
    let client = Client::new();
    let res = client.get(jwks_url).send().await?.json::<Value>().await?;
    Ok(res)
}

fn get_kid_from_token(token: &str) -> Result<String, Error> {
    let token_parts: Vec<&str> = token.split('.').collect();
    if token_parts.len() != 3 {
        return Err("Invalid JWT token".into());
    }

    let header = base64::decode(token_parts[0])?;
    let header_json: Value = serde_json::from_slice(&header)?;
    let kid = header_json["kid"]
        .as_str()
        .ok_or("No kid found in token header")?
        .to_string();

    Ok(kid)
}

fn get_decoding_key(kid: &str, jwks: &Value) -> Result<DecodingKey, Error> {
    let keys = jwks["keys"]
        .as_array()
        .ok_or("Invalid JWKS format: no 'keys' array")?;

    for key in keys {
        if key["kid"] == kid {
            let n = key["n"]
                .as_str()
                .ok_or("Invalid JWKS format: no 'n' value")?;
            let e = key["e"]
                .as_str()
                .ok_or("Invalid JWKS format: no 'e' value")?;

            let decoding_key = DecodingKey::from_rsa_components(n, e)?;
            return Ok(decoding_key);
        }
    }

    Err("No matching key found in JWKS".into())
}

async fn authorize(event: AuthEvent) -> Result<AuthResponse, Error> {
    let jwks_url = "https://auth-ex.eu.auth0.com//.well-known/jwks.json";
    let jwks = fetch_jwks(jwks_url).await?;

    let token = event.authorization_token;
    let kid = get_kid_from_token(&token)?;

    let decoding_key = get_decoding_key(&kid, &jwks)?;
    let mut validation = Validation::new(Algorithm::RS256);
    validation.set_audience(&["http://test-api-gw"]);

    let decoded_token = decode::<Value>(&token, &decoding_key, &validation)?;

    let policy_document = PolicyDocument {
        Version: "2012-10-17".to_string(),
        Statement: vec![Statement {
            Action: "execute-api:Invoke".to_string(),
            Effect: "Allow".to_string(),
            Resource: event.method_arn,
        }],
    };

    let auth_response = AuthResponse {
        principal_id: decoded_token.claims["sub"].as_str().unwrap_or("").to_string(),
        policy_document: policy_document,
    };

    Ok(auth_response)
}

#[tokio::main]
async fn main() -> Result<(), Error> {
    let func = service_fn(authorize);
    lambda_runtime::run(func).await;
}
