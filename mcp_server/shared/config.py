"""
Configuration management for MCP server implementations.

Provides base settings for both STDIO and cloud versions with
environment variable support and sensible defaults.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPBaseSettings(BaseSettings):
    """Base configuration shared between STDIO and cloud versions."""
    
    # API configuration
    api_base_url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    
    # Environment
    node_env: str = "development"
    
    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


class CloudSettings(BaseSettings):
    """Cloud-specific configuration for SSE MCP server."""
    
    # Inherit base settings
    api_base_url: str = "http://localhost:8080"
    api_key: Optional[str] = None
    node_env: str = "development"
    
    # MCP authentication
    mcp_api_key: Optional[str] = None
    
    # Authentication configuration
    auth_provider: str = "api_key"  # "api_key" or "oauth"
    
    # OAuth settings (future use)
    oauth_enabled: bool = False
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    
    # Transport configuration
    transport_type: str = "sse"  # "sse" or "streamable_http"
    
    # Server configuration
    host: str = "0.0.0.0"
    port: int = 8080
    
    # Cloud Run optimizations
    cloud_run_timeout: int = 840  # 14 minutes in seconds
    max_request_size: int = 32 * 1024 * 1024  # 32MB
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    
    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


def get_base_settings() -> MCPBaseSettings:
    """Get base settings instance."""
    return MCPBaseSettings()


def get_cloud_settings() -> CloudSettings:
    """Get cloud settings instance."""
    return CloudSettings()


def get_settings_for_environment() -> MCPBaseSettings:
    """
    Get appropriate settings based on environment.
    
    Returns CloudSettings in production or when MCP_CLOUD_MODE is set,
    otherwise returns BaseSettings.
    """
    cloud_mode = os.environ.get("MCP_CLOUD_MODE", "false").lower() == "true"
    is_production = os.environ.get("NODE_ENV", "development") == "production"
    
    if cloud_mode or is_production:
        return get_cloud_settings()
    else:
        return get_base_settings()