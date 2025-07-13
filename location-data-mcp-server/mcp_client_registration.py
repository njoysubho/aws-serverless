import json
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin
from dataclasses import dataclass, asdict

import httpx
from aws_lambda_powertools import Logger

logger = Logger()

@dataclass
class ClientRegistrationRequest:
    """OAuth 2.0 Dynamic Client Registration Request (RFC 7591)"""
    client_name: str
    redirect_uris: List[str]
    client_uri: Optional[str] = None
    logo_uri: Optional[str] = None
    contacts: Optional[List[str]] = None
    tos_uri: Optional[str] = None
    policy_uri: Optional[str] = None
    token_endpoint_auth_method: Optional[str] = "client_secret_basic"
    grant_types: Optional[List[str]] = None
    response_types: Optional[List[str]] = None
    scope: Optional[str] = None
    software_id: Optional[str] = None
    software_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

@dataclass
class ClientRegistrationResponse:
    """OAuth 2.0 Dynamic Client Registration Response (RFC 7591)"""
    client_id: str
    client_secret: Optional[str] = None
    client_secret_expires_at: Optional[int] = None
    registration_access_token: Optional[str] = None
    registration_client_uri: Optional[str] = None
    client_id_issued_at: Optional[int] = None
    client_name: Optional[str] = None
    redirect_uris: Optional[List[str]] = None
    token_endpoint_auth_method: Optional[str] = None
    grant_types: Optional[List[str]] = None
    response_types: Optional[List[str]] = None
    scope: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClientRegistrationResponse':
        return cls(**{k: v for k, v in data.items() if hasattr(cls, k)})

class MCPClientRegistrationHelper:
    """Helper utilities for MCP client registration with authorization servers"""
    
    def __init__(self, user_agent: str = "MCP-Server/1.0"):
        self.user_agent = user_agent
        
    async def discover_registration_endpoint(self, authorization_server_url: str) -> Optional[str]:
        """
        Discover the client registration endpoint for an authorization server
        
        Args:
            authorization_server_url: The authorization server base URL
            
        Returns:
            Registration endpoint URL or None if not supported
        """
        try:
            # Try OAuth 2.0 Authorization Server Metadata discovery
            discovery_url = urljoin(authorization_server_url, "/.well-known/oauth-authorization-server")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(discovery_url, timeout=30.0)
                response.raise_for_status()
                metadata = response.json()
                
                registration_endpoint = metadata.get("registration_endpoint")
                if registration_endpoint:
                    logger.info(f"Found registration endpoint: {registration_endpoint}")
                    return registration_endpoint
                else:
                    logger.warning(f"Authorization server {authorization_server_url} does not support dynamic client registration")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to discover registration endpoint for {authorization_server_url}: {str(e)}")
            return None
            
    async def register_client(self, 
                            registration_endpoint: str,
                            registration_request: ClientRegistrationRequest,
                            initial_access_token: Optional[str] = None) -> Optional[ClientRegistrationResponse]:
        """
        Register a client with an authorization server
        
        Args:
            registration_endpoint: The registration endpoint URL
            registration_request: Client registration request data
            initial_access_token: Optional initial access token for registration
            
        Returns:
            Client registration response or None if failed
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": self.user_agent,
                "Accept": "application/json"
            }
            
            # Add initial access token if provided
            if initial_access_token:
                headers["Authorization"] = f"Bearer {initial_access_token}"
                
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    registration_endpoint,
                    headers=headers,
                    json=registration_request.to_dict(),
                    timeout=30.0
                )
                response.raise_for_status()
                
                registration_response = ClientRegistrationResponse.from_dict(response.json())
                logger.info(f"Successfully registered client: {registration_response.client_id}")
                return registration_response
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                logger.error(f"Invalid client registration request - status: {e.response.status_code}")
            elif e.response.status_code == 401:
                logger.error("Invalid or missing initial access token")
            elif e.response.status_code == 403:
                logger.error("Client registration not allowed")
            else:
                logger.error(f"Client registration failed with status {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Client registration failed: {str(e)}")
            return None
            
    async def discover_and_register_with_servers(self,
                                               authorization_servers: List[str],
                                               client_name: str,
                                               redirect_uris: List[str],
                                               required_scopes: Optional[List[str]] = None,
                                               **kwargs) -> Dict[str, Optional[ClientRegistrationResponse]]:
        """
        Discover registration endpoints and register with multiple authorization servers
        
        Args:
            authorization_servers: List of authorization server URLs
            client_name: Name of the client application
            redirect_uris: List of redirect URIs
            required_scopes: List of required scopes
            **kwargs: Additional client registration parameters
            
        Returns:
            Dictionary mapping server URLs to registration responses
        """
        results: Dict[str, Optional[ClientRegistrationResponse]] = {}
        
        # Prepare registration request
        registration_request = ClientRegistrationRequest(
            client_name=client_name,
            redirect_uris=redirect_uris,
            scope=" ".join(required_scopes) if required_scopes else None,
            grant_types=["authorization_code"],
            response_types=["code"],
            token_endpoint_auth_method="client_secret_basic",
            **kwargs
        )
        
        for server_url in authorization_servers:
            try:
                # Discover registration endpoint
                registration_endpoint = await self.discover_registration_endpoint(server_url)
                
                if registration_endpoint:
                    # Attempt registration
                    registration_response = await self.register_client(
                        registration_endpoint, 
                        registration_request
                    )
                    results[server_url] = registration_response
                else:
                    logger.warning(f"Server {server_url} does not support dynamic client registration")
                    results[server_url] = None
                    
            except Exception as e:
                logger.error(f"Failed to register with server {server_url}: {str(e)}")
                results[server_url] = None
                
        return results
        
    def get_authorization_url(self, 
                            authorization_endpoint: str,
                            client_id: str,
                            redirect_uri: str,
                            scope: str,
                            state: str,
                            code_challenge: str,
                            code_challenge_method: str = "S256",
                            resource: Optional[str] = None) -> str:
        """
        Generate authorization URL for OAuth 2.1 with PKCE
        
        Args:
            authorization_endpoint: Authorization endpoint URL
            client_id: Registered client ID
            redirect_uri: Redirect URI
            scope: Requested scopes
            state: State parameter for CSRF protection
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE challenge method
            resource: Resource parameter (RFC 8707)
            
        Returns:
            Authorization URL
        """
        from urllib.parse import urlencode
        
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method
        }
        
        # Add resource parameter if provided (RFC 8707)
        if resource:
            params["resource"] = resource
            
        return f"{authorization_endpoint}?{urlencode(params)}"

def create_mcp_client_registration_helper(user_agent: str = "MCP-Server/1.0") -> MCPClientRegistrationHelper:
    """Factory function to create MCP client registration helper"""
    return MCPClientRegistrationHelper(user_agent=user_agent)

# Utility functions for PKCE
def generate_pkce_pair() -> Tuple[str, str]:
    """Generate PKCE code verifier and challenge pair"""
    import secrets
    import base64
    import hashlib
    
    # Generate code verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    
    # Generate code challenge (SHA256 hash of verifier)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    return code_verifier, code_challenge

def generate_state() -> str:
    """Generate random state parameter for CSRF protection"""
    import secrets
    return secrets.token_urlsafe(32) 