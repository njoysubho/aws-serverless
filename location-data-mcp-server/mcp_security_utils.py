"""
Security utilities for MCP authorization implementation
"""
import json
import re
from typing import Any, Dict, List, Optional, Union

# Sensitive patterns that should be redacted
SENSITIVE_PATTERNS = {
    'authorization_header': re.compile(r'Bearer\s+[A-Za-z0-9\-\._~\+\/]+=*', re.IGNORECASE),
    'jwt_token': re.compile(r'ey[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]*'),
    'api_key': re.compile(r'["\']?(?:api_key|apikey|key)["\']?\s*[:=]\s*["\']?([A-Za-z0-9\-_]{10,})["\']?', re.IGNORECASE),
    'client_secret': re.compile(r'["\']?(?:client_secret|secret)["\']?\s*[:=]\s*["\']?([A-Za-z0-9\-_]{10,})["\']?', re.IGNORECASE),
    'access_token': re.compile(r'["\']?(?:access_token|token)["\']?\s*[:=]\s*["\']?([A-Za-z0-9\-_]{10,})["\']?', re.IGNORECASE),
}

# Headers that should be redacted
SENSITIVE_HEADERS = {
    'authorization',
    'x-api-key',
    'x-auth-token',
    'x-access-token',
    'cookie',
    'set-cookie',
    'x-amz-security-token',
    'x-amz-session-token'
}

# Query parameters that should be redacted
SENSITIVE_QUERY_PARAMS = {
    'access_token',
    'api_key',
    'apikey',
    'key',
    'token',
    'secret',
    'password',
    'client_secret'
}

def redact_sensitive_data(data: Any, max_length: int = 1000) -> Any:
    """
    Recursively redact sensitive data from any data structure
    
    Args:
        data: Data to redact (dict, list, string, etc.)
        max_length: Maximum length for string values
        
    Returns:
        Data with sensitive information redacted
    """
    if isinstance(data, dict):
        return {k: redact_sensitive_data(v, max_length) for k, v in data.items()}
    elif isinstance(data, list):
        return [redact_sensitive_data(item, max_length) for item in data]
    elif isinstance(data, str):
        return redact_sensitive_string(data, max_length)
    else:
        return data

def redact_sensitive_string(text: str, max_length: int = 1000) -> str:
    """
    Redact sensitive information from strings
    
    Args:
        text: String to redact
        max_length: Maximum length for the string
        
    Returns:
        String with sensitive information redacted
    """
    if not isinstance(text, str):
        return text
        
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "...[truncated]"
    
    # Apply redaction patterns
    for pattern_name, pattern in SENSITIVE_PATTERNS.items():
        text = pattern.sub('[REDACTED]', text)
    
    return text

def sanitize_lambda_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize Lambda event for safe logging
    
    Args:
        event: Lambda event dictionary
        
    Returns:
        Sanitized event dictionary
    """
    sanitized = {}
    
    for key, value in event.items():
        if key in ['headers', 'multiValueHeaders']:
            # Sanitize headers
            sanitized[key] = sanitize_headers(value)
        elif key == 'queryStringParameters':
            # Sanitize query parameters
            sanitized[key] = sanitize_query_params(value)
        elif key == 'body':
            # Sanitize body content
            sanitized[key] = sanitize_body(value)
        elif key == 'requestContext':
            # Keep request context but sanitize identity
            sanitized[key] = sanitize_request_context(value)
        else:
            # Keep other fields as-is
            sanitized[key] = value
    
    return sanitized

def sanitize_headers(headers: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Sanitize HTTP headers for safe logging
    
    Args:
        headers: Headers dictionary
        
    Returns:
        Sanitized headers dictionary
    """
    if not headers:
        return headers
        
    sanitized = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADERS:
            sanitized[key] = '[REDACTED]'
        else:
            sanitized[key] = str(value)
    
    return sanitized

def sanitize_query_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """
    Sanitize query parameters for safe logging
    
    Args:
        params: Query parameters dictionary
        
    Returns:
        Sanitized parameters dictionary
    """
    if not params:
        return params
        
    sanitized = {}
    for key, value in params.items():
        if key.lower() in SENSITIVE_QUERY_PARAMS:
            sanitized[key] = '[REDACTED]'
        else:
            sanitized[key] = str(value)
    
    return sanitized

def sanitize_body(body: Optional[str]) -> Optional[str]:
    """
    Sanitize request body for safe logging
    
    Args:
        body: Request body string
        
    Returns:
        Sanitized body string
    """
    if not body:
        return body
        
    try:
        # Try to parse as JSON and sanitize
        body_dict = json.loads(body)
        sanitized_dict = redact_sensitive_data(body_dict)
        return json.dumps(sanitized_dict)
    except json.JSONDecodeError:
        # If not JSON, apply string redaction
        return redact_sensitive_string(body)

def sanitize_request_context(context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Sanitize request context for safe logging
    
    Args:
        context: Request context dictionary
        
    Returns:
        Sanitized context dictionary
    """
    if not context:
        return context
        
    sanitized = dict(context)
    
    # Remove sensitive identity information
    if 'identity' in sanitized:
        identity = sanitized['identity']
        if isinstance(identity, dict):
            # Keep only non-sensitive identity fields
            safe_identity = {
                'sourceIp': identity.get('sourceIp', '[REDACTED]'),
                'userAgent': identity.get('userAgent', '[REDACTED]'),
                'requestId': identity.get('requestId')
            }
            sanitized['identity'] = safe_identity
    
    return sanitized

def safe_log_event(event: Dict[str, Any], max_size: int = 5000) -> Dict[str, Any]:
    """
    Create a safe-to-log version of a Lambda event
    
    Args:
        event: Original Lambda event
        max_size: Maximum size for the logged event
        
    Returns:
        Safe-to-log event dictionary
    """
    sanitized = sanitize_lambda_event(event)
    
    # Convert to JSON string to check size
    json_str = json.dumps(sanitized, default=str)
    
    if len(json_str) > max_size:
        # If still too large, keep only essential fields
        essential_fields = ['httpMethod', 'path', 'requestContext', 'isBase64Encoded']
        sanitized = {k: v for k, v in sanitized.items() if k in essential_fields}
        json_str = json.dumps(sanitized, default=str)
        
        if len(json_str) > max_size:
            # If still too large, return minimal info
            return {
                'httpMethod': event.get('httpMethod', 'UNKNOWN'),
                'path': event.get('path', 'UNKNOWN'),
                'requestId': event.get('requestContext', {}).get('requestId', 'UNKNOWN'),
                '_truncated': True
            }
    
    return sanitized

def mask_client_secret(client_secret: Optional[str]) -> str:
    """
    Safely mask client secret for logging
    
    Args:
        client_secret: Client secret string
        
    Returns:
        Masked client secret
    """
    if not client_secret:
        return "None"
    
    if len(client_secret) <= 8:
        return "*" * len(client_secret)
    
    return client_secret[:4] + "*" * (len(client_secret) - 8) + client_secret[-4:]

def safe_error_message(error: Exception) -> str:
    """
    Create a safe error message that doesn't leak sensitive information
    
    Args:
        error: Exception object
        
    Returns:
        Safe error message
    """
    error_type = type(error).__name__
    error_message = str(error)
    
    # Redact sensitive information from error message
    safe_message = redact_sensitive_string(error_message)
    
    # Don't include the full error message if it's too long
    if len(safe_message) > 200:
        safe_message = safe_message[:200] + "...[truncated]"
    
    return f"{error_type}: {safe_message}"

# Quick helper functions for common use cases
def log_safe_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Quick helper to get safe event for logging"""
    return safe_log_event(event)

def log_safe_error(error: Exception) -> str:
    """Quick helper to get safe error message"""
    return safe_error_message(error) 