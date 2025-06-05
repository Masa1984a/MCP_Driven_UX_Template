"""
Authentication provider abstraction for MCP server.

Provides a common interface for different authentication methods
including API key and future OAuth implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class AuthResult:
    """Result of authentication attempt."""
    success: bool
    user_id: Optional[str] = None
    user_info: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class AuthProvider(ABC):
    """Abstract base class for authentication providers."""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """
        Authenticate user with provided credentials.
        
        Args:
            credentials: Authentication credentials (format depends on provider)
            
        Returns:
            AuthResult with success status and user information
        """
        pass
    
    @abstractmethod
    def get_auth_headers(self, credentials: Dict[str, Any]) -> Dict[str, str]:
        """
        Get HTTP headers for authenticated requests.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Dictionary of HTTP headers
        """
        pass
    
    @abstractmethod
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        Validate credential format without making external calls.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if credentials are properly formatted
        """
        pass


class APIKeyAuthProvider(AuthProvider):
    """API key authentication provider."""
    
    def __init__(self, api_key_header: str = "x-api-key"):
        """
        Initialize API key auth provider.
        
        Args:
            api_key_header: HTTP header name for API key
        """
        self.api_key_header = api_key_header
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """
        Authenticate using API key.
        
        Args:
            credentials: Dict with 'api_key' field
            
        Returns:
            AuthResult with authentication status
        """
        api_key = credentials.get('api_key')
        
        if not api_key:
            return AuthResult(
                success=False,
                error_message="API key not provided"
            )
        
        # For API key auth, we assume the key is valid if provided
        # Real validation would happen on the API server side
        return AuthResult(
            success=True,
            user_id="api_key_user",  # Placeholder user ID
            user_info={"auth_method": "api_key"}
        )
    
    def get_auth_headers(self, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Get headers for API key authentication."""
        api_key = credentials.get('api_key')
        
        if not api_key:
            return {}
        
        return {
            self.api_key_header: api_key,
            'Content-Type': 'application/json'
        }
    
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate API key credentials format."""
        api_key = credentials.get('api_key')
        return isinstance(api_key, str) and len(api_key.strip()) > 0


class NoAuthProvider(AuthProvider):
    """No authentication provider for development/testing."""
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """Always allow access without authentication."""
        return AuthResult(
            success=True,
            user_id="anonymous",
            user_info={"auth_method": "none"}
        )
    
    def get_auth_headers(self, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Get headers without authentication."""
        return {'Content-Type': 'application/json'}
    
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """No validation needed for no-auth."""
        return True


class AuthManager:
    """
    Authentication manager that handles different auth providers.
    
    Provides a unified interface for authentication regardless of the
    underlying authentication method.
    """
    
    def __init__(self, provider: AuthProvider):
        """
        Initialize auth manager with a provider.
        
        Args:
            provider: Authentication provider instance
        """
        self.provider = provider
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthResult:
        """Authenticate using the configured provider."""
        return await self.provider.authenticate(credentials)
    
    def get_auth_headers(self, credentials: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers."""
        return self.provider.get_auth_headers(credentials)
    
    def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate credentials format."""
        return self.provider.validate_credentials(credentials)


def create_auth_manager(auth_type: str, **kwargs) -> AuthManager:
    """
    Factory function to create auth manager with specified provider.
    
    Args:
        auth_type: Type of authentication ("api_key", "none", "oauth")
        **kwargs: Additional arguments for the provider
        
    Returns:
        Configured AuthManager instance
        
    Raises:
        ValueError: If auth_type is not supported
    """
    if auth_type == "api_key":
        provider = APIKeyAuthProvider(**kwargs)
    elif auth_type == "none":
        provider = NoAuthProvider()
    elif auth_type == "oauth":
        # Future OAuth implementation
        raise NotImplementedError("OAuth authentication not yet implemented")
    else:
        raise ValueError(f"Unsupported authentication type: {auth_type}")
    
    return AuthManager(provider)