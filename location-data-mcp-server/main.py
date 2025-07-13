import json
import os
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP
import aws_util

from aws_lambda_powertools import Logger
from awslabs.mcp_lambda_handler import MCPLambdaHandler

# Import authorization components
from mcp_auth_decorator import with_mcp_authorization, with_mcp_authorization_from_config
from mcp_security_utils import log_safe_event

logger = Logger()

mcp = MCPLambdaHandler(name="location-data-mcp-server")

# Shared utility function
def do_get(url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    headers = {"Accept": "application/json"}

    with httpx.Client()  as client:
        try:
            response = client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


@mcp.tool()
def get_nearby_pois(address: str) -> str:
    """Fetch nearby points of interest given an address
    Args:
       address (str): The address to search for nearby POIs.
       Example: {"address": "1600 Pennsylvania Ave NW, Washington, DC 20500"}
    Returns:
        str: A JSON string containing the nearby POIs.
    
    """
    logger.info(f"Fetching nearby POIs for address: {address}")
    try:
        geocode = get_geocoding(address)
        # Log safe geocoding info (without potential API keys)
        if geocode and "results" in geocode and geocode["results"]:
            logger.info(f"Geocoding successful - found {len(geocode['results'])} results")
        else:
            logger.warning("Geocoding returned no results")
        latitude = geocode["results"][0]["position"]["lat"]
        longitude = geocode["results"][0]["position"]["lon"]
        api_key = aws_util.get_secret("/location/tomtom")
        url = "https://api.tomtom.com/search/2/nearbySearch/.json"
        params = {"lat": latitude, "lon": longitude, "key": api_key}
        response = do_get(url, params=params)

        if response is None:
            return json.dumps({"error": "Failed to fetch nearby POIs"})

        return json.dumps(response)
    except Exception as e:
        logger.error(f"Error fetching POIs: {str(e)}")
        return json.dumps({"error": f"Error fetching POIs: {str(e)}"})


def get_geocoding(address: str):
    """
    Fetch The address to geocode.
    """
    try:
        api_key = aws_util.get_secret("/location/tomtom")
        url = "https://api.tomtom.com/search/2/geocode/.json"
        params = {"key": api_key, "query": address}
        response = do_get(url, params=params)
        if response is None:
            return json.dumps({"error": "Failed to fetch geocoding information"})
        return response
    except Exception as e:
        logger.error(f"Error fetching geocoding information: {str(e)}")
        return json.dumps({"error": f"Error fetching geocoding information: {str(e)}"})


# Example 1: Manual authorization configuration
@with_mcp_authorization(
    resource_id="location-data-mcp-server",
    authorization_servers=["https://auth.example.com"],
    required_scopes=["mcp:location:read"],
    audience="location-data-api",
    enable_authorization=os.getenv("ENABLE_MCP_AUTH", "false").lower() == "true"
)
def lambda_handler_with_auth(event, context):
    """Lambda handler with manual authorization configuration"""
    # Log safe event information (without Authorization headers)
    logger.info(f"Processing request: {log_safe_event(event)}")
    
    # Token payload is available in event if authorization is enabled
    if "mcp_token_payload" in event:
        logger.info(f"Authenticated user: {event['mcp_token_payload'].get('sub', 'unknown')}")
    
    return mcp.handle_request(event, context)


# Example 2: Configuration-based authorization (recommended for production)
@with_mcp_authorization_from_config(config_key="/mcp/location-data/auth-config")
def lambda_handler_with_config_auth(event, context):
    """Lambda handler with configuration-based authorization"""
    # Log safe event information (without Authorization headers)
    logger.info(f"Processing request: {log_safe_event(event)}")
    
    # Token payload is available in event if authorization is enabled
    if "mcp_token_payload" in event:
        token_payload = event["mcp_token_payload"]
        logger.info(f"Authenticated user: {token_payload.get('sub', 'unknown')}")
        logger.info(f"Token scopes: {token_payload.get('scope', '')}")
    
    return mcp.handle_request(event, context)


# Default handler without authorization (for backward compatibility)
def lambda_handler(event, context):
    """Default Lambda handler without authorization"""
    # Log safe event information (without Authorization headers)
    logger.info(f"Processing request: {log_safe_event(event)}")
    return mcp.handle_request(event, context)


# Use the configuration-based auth handler as default
# This can be overridden by setting the handler in template.yaml
lambda_handler = lambda_handler_with_config_auth