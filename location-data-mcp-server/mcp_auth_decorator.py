import asyncio
from functools import wraps
from typing import Any, Dict, List, Optional, Callable

from mcp_authorization import create_mcp_authorization, MCPAuthorizationMiddleware

def with_mcp_authorization(
    resource_id: str,
    authorization_servers: List[str],
    required_scopes: Optional[List[str]] = None,
    audience: Optional[str] = None,
    resource_metadata_url: Optional[str] = None,
    enable_authorization: bool = True
):
    """
    Decorator to add MCP authorization to Lambda handlers
    
    Args:
        resource_id: Unique identifier for this resource
        authorization_servers: List of OAuth 2.1 authorization servers
        required_scopes: List of required scopes for access
        audience: Expected audience for tokens
        resource_metadata_url: URL for protected resource metadata endpoint
        enable_authorization: Whether to enable authorization (useful for dev/test)
    """
    def decorator(handler_func: Callable) -> Callable:
        if not enable_authorization:
            return handler_func
            
        # Create authorization middleware
        auth_middleware = create_mcp_authorization(
            resource_id=resource_id,
            authorization_servers=authorization_servers,
            required_scopes=required_scopes,
            audience=audience,
            resource_metadata_url=resource_metadata_url
        )
        
        @wraps(handler_func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            # Handle sync/async handlers
            if asyncio.iscoroutinefunction(handler_func):
                return asyncio.run(auth_middleware(event, context, handler_func))
            else:
                # Wrap sync handler for async middleware
                async def async_handler(event, context):
                    return handler_func(event, context)
                return asyncio.run(auth_middleware(event, context, async_handler))
                
        return wrapper
    return decorator

def with_mcp_authorization_from_config(config_key: str = "MCP_AUTH_CONFIG"):
    """
    Decorator that reads authorization config from environment/parameter store
    
    Args:
        config_key: Parameter Store key for authorization configuration
    """
    def decorator(handler_func: Callable) -> Callable:
        @wraps(handler_func)
        def wrapper(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
            import os
            import json
            from aws_util import get_secret
            
            # Try to get config from environment first, then parameter store
            config_json = os.environ.get(config_key)
            if not config_json:
                try:
                    config_json = get_secret(config_key)
                except Exception:
                    # If no config found, proceed without authorization
                    return handler_func(event, context)
            
            if not config_json:
                return handler_func(event, context)
                
            try:
                config = json.loads(config_json)
                
                # Apply authorization with config
                auth_decorator = with_mcp_authorization(
                    resource_id=config.get("resource_id", "mcp-server"),
                    authorization_servers=config.get("authorization_servers", []),
                    required_scopes=config.get("required_scopes"),
                    audience=config.get("audience"),
                    resource_metadata_url=config.get("resource_metadata_url"),
                    enable_authorization=config.get("enable_authorization", True)
                )
                
                return auth_decorator(handler_func)(event, context)
                
            except (json.JSONDecodeError, KeyError) as e:
                # If config is invalid, log and proceed without authorization
                import logging
                logging.warning(f"Invalid authorization config: {e}")
                return handler_func(event, context)
                
        return wrapper
    return decorator 