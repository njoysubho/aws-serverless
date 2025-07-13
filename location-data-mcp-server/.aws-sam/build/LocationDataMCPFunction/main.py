import json
from typing import Any, Dict, Optional

import httpx
from mcp.server.fastmcp import FastMCP
import aws_util

from aws_lambda_powertools import Logger
from awslabs.mcp_lambda_handler import MCPLambdaHandler


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
    logger.info(f"Fetching nearby POIs for address: address")
    try:
        geocode = get_geocoding(address)
        logger.info(f"Geocoding response: {geocode}")
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


def lambda_handler(event,context):
    logger.info(f"Event: {event}")
    return mcp.handle_request(event, context)