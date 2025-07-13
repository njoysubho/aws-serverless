import json
import time
import base64
from typing import Any, Dict, Optional, List, Tuple
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass, asdict
from enum import Enum

import httpx
import jwt
from jwt.exceptions import InvalidTokenError as JWTInvalidTokenError
from aws_lambda_powertools import Logger

logger = Logger()

class AuthorizationError(Exception):
    """Base authorization error"""
    pass

class InvalidTokenError(AuthorizationError):
    """Invalid token error"""
    pass

class InsufficientScopeError(AuthorizationError):
    """Insufficient scope error"""
    pass

class TokenExpiredError(AuthorizationError):
    """Token expired error"""
    pass

@dataclass
class ProtectedResourceMetadata:
    """OAuth 2.0 Protected Resource Metadata (RFC 9728)"""
    resource: str
    authorization_servers: List[str]
    scopes_supported: Optional[List[str]] = None
    bearer_methods_supported: Optional[List[str]] = None
    resource_documentation: Optional[str] = None
    resource_policy_uri: Optional[str] = None
    resource_tos_uri: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class AuthorizationServerMetadata:
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
    issuer: str
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    registration_endpoint: Optional[str] = None
    scopes_supported: Optional[List[str]] = None
    response_types_supported: Optional[List[str]] = None
    grant_types_supported: Optional[List[str]] = None
    token_endpoint_auth_methods_supported: Optional[List[str]] = None
    introspection_endpoint: Optional[str] = None
    revocation_endpoint: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

class MCPAuthorizationServer:
    """MCP Authorization Server implementing OAuth 2.1 standards"""
    
    def __init__(self, 
                 resource_id: str,
                 authorization_servers: List[str],
                 required_scopes: Optional[List[str]] = None,
                 audience: Optional[str] = None,
                 resource_metadata_url: Optional[str] = None):
        self.resource_id = resource_id
        self.authorization_servers = authorization_servers
        self.required_scopes = required_scopes or []
        self.audience = audience
        self.resource_metadata_url = resource_metadata_url or "/.well-known/oauth-protected-resource"
        self._jwks_cache: Dict[str, Dict[str, Any]] = {}
        self._jwks_cache_expiry: Dict[str, float] = {}
        self._auth_server_metadata_cache: Dict[str, AuthorizationServerMetadata] = {}
        
    def get_protected_resource_metadata(self) -> ProtectedResourceMetadata:
        """Get protected resource metadata per RFC 9728"""
        return ProtectedResourceMetadata(
            resource=self.resource_id,
            authorization_servers=self.authorization_servers,
            scopes_supported=self.required_scopes if self.required_scopes else None,
            bearer_methods_supported=["header", "query"],
            resource_documentation=f"https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization"
        )
        
    async def get_client_registration_info(self) -> Dict[str, Any]:
        """
        Get client registration information for all configured authorization servers
        
        Returns:
            Dictionary with registration endpoints and support information
        """
        registration_info = {
            "supported_servers": [],
            "unsupported_servers": []
        }
        
        for server_url in self.authorization_servers:
            try:
                metadata = await self.discover_authorization_server(server_url)
                if metadata.registration_endpoint:
                    registration_info["supported_servers"].append({
                        "server": server_url,
                        "registration_endpoint": metadata.registration_endpoint,
                        "supported_scopes": metadata.scopes_supported,
                        "supported_response_types": metadata.response_types_supported,
                        "supported_grant_types": metadata.grant_types_supported
                    })
                else:
                    registration_info["unsupported_servers"].append(server_url)
            except Exception as e:
                logger.warning(f"Failed to get registration info for {server_url}: {str(e)}")
                registration_info["unsupported_servers"].append(server_url)
                
        return registration_info
        
    async def discover_authorization_server(self, server_url: str) -> AuthorizationServerMetadata:
        """Discover authorization server metadata per RFC 8414"""
        if server_url in self._auth_server_metadata_cache:
            return self._auth_server_metadata_cache[server_url]
            
        discovery_url = urljoin(server_url, "/.well-known/oauth-authorization-server")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(discovery_url, timeout=30.0)
                response.raise_for_status()
                metadata_dict = response.json()
                
                metadata = AuthorizationServerMetadata(
                    issuer=metadata_dict["issuer"],
                    authorization_endpoint=metadata_dict.get("authorization_endpoint"),
                    token_endpoint=metadata_dict.get("token_endpoint"),
                    jwks_uri=metadata_dict.get("jwks_uri"),
                    registration_endpoint=metadata_dict.get("registration_endpoint"),
                    scopes_supported=metadata_dict.get("scopes_supported"),
                    response_types_supported=metadata_dict.get("response_types_supported"),
                    grant_types_supported=metadata_dict.get("grant_types_supported"),
                    token_endpoint_auth_methods_supported=metadata_dict.get("token_endpoint_auth_methods_supported"),
                    introspection_endpoint=metadata_dict.get("introspection_endpoint"),
                    revocation_endpoint=metadata_dict.get("revocation_endpoint")
                )
                
                self._auth_server_metadata_cache[server_url] = metadata
                return metadata
                
            except Exception as e:
                logger.error(f"Failed to discover authorization server metadata: {str(e)}")
                raise AuthorizationError(f"Authorization server discovery failed: {str(e)}")
                
    async def get_jwks(self, jwks_uri: str) -> Dict[str, Any]:
        """Get JWKS with caching"""
        current_time = time.time()
        
        if (jwks_uri in self._jwks_cache and 
            jwks_uri in self._jwks_cache_expiry and
            current_time < self._jwks_cache_expiry[jwks_uri]):
            return self._jwks_cache[jwks_uri]
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(jwks_uri, timeout=30.0)
                response.raise_for_status()
                jwks = response.json()
                
                self._jwks_cache[jwks_uri] = jwks
                self._jwks_cache_expiry[jwks_uri] = current_time + 3600  # Cache for 1 hour
                
                return jwks
                
            except Exception as e:
                logger.error(f"Failed to fetch JWKS: {str(e)}")
                raise AuthorizationError(f"JWKS fetch failed: {str(e)}")
                
    async def validate_token(self, access_token: str) -> Dict[str, Any]:
        """Validate access token according to OAuth 2.1 and MCP specification"""
        try:
            # Decode token without verification first to get issuer
            unverified_payload = jwt.decode(access_token, options={"verify_signature": False})
            issuer = unverified_payload.get("iss")
            
            if not issuer:
                raise InvalidTokenError("Token missing issuer")
                
            # Find matching authorization server
            auth_server = None
            for server_url in self.authorization_servers:
                try:
                    metadata = await self.discover_authorization_server(server_url)
                    if metadata.issuer == issuer:
                        auth_server = metadata
                        break
                except Exception:
                    continue
                    
            if not auth_server:
                raise InvalidTokenError("Token issuer not in authorized servers")
                
            # Get JWKS and validate token
            if not auth_server.jwks_uri:
                raise InvalidTokenError("Authorization server missing JWKS URI")
                
            jwks = await self.get_jwks(auth_server.jwks_uri)
            
            # Validate token signature and claims
            try:
                payload = jwt.decode(
                    access_token,
                    jwks,
                    algorithms=["RS256", "ES256", "PS256"],
                    audience=self.audience,
                    issuer=issuer,
                    options={"verify_exp": True, "verify_aud": True if self.audience else False}
                )
            except jwt.ExpiredSignatureError:
                raise TokenExpiredError("Token has expired")
            except jwt.InvalidAudienceError:
                raise InvalidTokenError("Token audience invalid")
            except jwt.InvalidIssuerError:
                raise InvalidTokenError("Token issuer invalid")
            except JWTInvalidTokenError as e:
                raise InvalidTokenError(f"Token validation failed: {str(e)}")
                
            # Validate scopes if required
            if self.required_scopes:
                token_scopes = payload.get("scope", "").split()
                if not all(scope in token_scopes for scope in self.required_scopes):
                    raise InsufficientScopeError("Insufficient token scope")
                    
            return payload
            
        except AuthorizationError:
            raise
        except Exception as e:
            logger.error(f"Token validation error: {type(e).__name__}")
            raise InvalidTokenError(f"Token validation failed: {type(e).__name__}")
            
    def extract_token_from_request(self, event: Dict[str, Any]) -> Optional[str]:
        """Extract bearer token from Lambda event"""
        # Check Authorization header
        headers = event.get("headers", {})
        auth_header = headers.get("Authorization") or headers.get("authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # Remove "Bearer " prefix
            
        # Check query parameters
        query_params = event.get("queryStringParameters") or {}
        if "access_token" in query_params:
            return query_params["access_token"]
            
        return None
        
    def create_www_authenticate_header(self, error: str = "invalid_token", 
                                     error_description: Optional[str] = None) -> str:
        """Create WWW-Authenticate header per RFC 6750 and RFC 9728"""
        header_parts = [f'Bearer realm="{self.resource_id}"']
        header_parts.append(f'as_uri="{self.resource_metadata_url}"')
        header_parts.append(f'error="{error}"')
        
        if error_description:
            header_parts.append(f'error_description="{error_description}"')
            
        if self.required_scopes:
            scope_string = " ".join(self.required_scopes)
            header_parts.append(f'scope="{scope_string}"')
            
        return ", ".join(header_parts)
        
    def create_error_response(self, status_code: int, error: str, 
                            error_description: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        headers = {"Content-Type": "application/json"}
        
        # Only include WWW-Authenticate header for 401 Unauthorized responses
        if status_code == 401:
            headers["WWW-Authenticate"] = self.create_www_authenticate_header(error, error_description)
        
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps({
                "error": error,
                "error_description": error_description or error
            })
        }

class MCPAuthorizationMiddleware:
    """MCP Authorization Middleware for Lambda functions"""
    
    def __init__(self, auth_server: MCPAuthorizationServer):
        self.auth_server = auth_server
        
    async def __call__(self, event: Dict[str, Any], context: Any, 
                      handler_func: callable) -> Dict[str, Any]:
        """Middleware to handle authorization for MCP servers"""
        try:
            # Handle well-known endpoints
            path = event.get("path", "")
            if path == "/.well-known/oauth-protected-resource":
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(self.auth_server.get_protected_resource_metadata().to_dict())
                }
            elif path == "/.well-known/client-registration-info":
                registration_info = await self.auth_server.get_client_registration_info()
                return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(registration_info)
                }
                
            # Extract and validate token
            access_token = self.auth_server.extract_token_from_request(event)
            if not access_token:
                return self.auth_server.create_error_response(
                    401, "invalid_request", "Access token is required"
                )
                
            # Validate token
            token_payload = await self.auth_server.validate_token(access_token)
            
            # Add token payload to event for handler use
            event["mcp_token_payload"] = token_payload
            
            # Call original handler
            return await handler_func(event, context)
            
        except TokenExpiredError as e:
            return self.auth_server.create_error_response(
                401, "invalid_token", "Token has expired"
            )
        except InsufficientScopeError as e:
            return self.auth_server.create_error_response(
                403, "insufficient_scope", "Insufficient scope for this resource"
            )
        except InvalidTokenError as e:
            return self.auth_server.create_error_response(
                401, "invalid_token", str(e)
            )
        except AuthorizationError as e:
            return self.auth_server.create_error_response(
                401, "invalid_token", str(e)
            )
        except Exception as e:
            logger.error(f"Authorization middleware error: {str(e)}")
            return self.auth_server.create_error_response(
                500, "server_error", "Internal server error"
            )

def create_mcp_authorization(resource_id: str, 
                           authorization_servers: List[str],
                           required_scopes: Optional[List[str]] = None,
                           audience: Optional[str] = None,
                           resource_metadata_url: Optional[str] = None) -> MCPAuthorizationMiddleware:
    """Factory function to create MCP authorization middleware"""
    auth_server = MCPAuthorizationServer(
        resource_id=resource_id,
        authorization_servers=authorization_servers,
        required_scopes=required_scopes,
        audience=audience,
        resource_metadata_url=resource_metadata_url
    )
    return MCPAuthorizationMiddleware(auth_server) 