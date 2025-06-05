"""
Shared API client for MCP server implementations.

Provides common HTTP client functionality for both STDIO and cloud versions
with proper authentication and error handling.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Union
from urllib.parse import urljoin, urlencode

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Fallback to requests for sync usage
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class APIClientError(Exception):
    """Base exception for API client errors."""
    pass


class APIClient:
    """
    HTTP client for ticket API with authentication and error handling.
    
    Supports both sync and async operations depending on available libraries.
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize API client.
        
        Args:
            base_url: Base URL for the API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        
        # Choose the best available HTTP client
        if HTTPX_AVAILABLE:
            self._async_client = httpx.AsyncClient(timeout=timeout)
            self._sync_client = httpx.Client(timeout=timeout)
            self._client_type = "httpx"
        elif AIOHTTP_AVAILABLE:
            self._async_client = None  # Will be created per request
            self._sync_client = None
            self._client_type = "aiohttp"
        elif REQUESTS_AVAILABLE:
            self._async_client = None
            self._sync_client = requests.Session()
            self._sync_client.timeout = timeout
            self._client_type = "requests"
        else:
            raise APIClientError("No HTTP client library available. Install httpx, aiohttp, or requests.")
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests including authentication."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'MCP-Server/1.0'
        }
        
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        return headers
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith('http'):
            return endpoint
        return urljoin(self.base_url + '/', endpoint.lstrip('/'))
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make async GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIClientError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self.get_headers()
        
        try:
            if self._client_type == "httpx":
                response = await self._async_client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            
            elif self._client_type == "aiohttp":
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(url, headers=headers, params=params) as response:
                        response.raise_for_status()
                        return await response.json()
            
            else:
                # Fallback to sync requests (not ideal for async context)
                response = self._sync_client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise APIClientError(f"GET request failed: {str(e)}") from e
    
    async def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make async POST request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIClientError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self.get_headers()
        json_data = json.dumps(data) if data else None
        
        try:
            if self._client_type == "httpx":
                response = await self._async_client.post(url, headers=headers, content=json_data)
                response.raise_for_status()
                return response.json()
            
            elif self._client_type == "aiohttp":
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.post(url, headers=headers, data=json_data) as response:
                        response.raise_for_status()
                        return await response.json()
            
            else:
                # Fallback to sync requests
                response = self._sync_client.post(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise APIClientError(f"POST request failed: {str(e)}") from e
    
    async def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make async PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            APIClientError: On request failure
        """
        url = self._build_url(endpoint)
        headers = self.get_headers()
        json_data = json.dumps(data) if data else None
        
        try:
            if self._client_type == "httpx":
                response = await self._async_client.put(url, headers=headers, content=json_data)
                response.raise_for_status()
                return response.json()
            
            elif self._client_type == "aiohttp":
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.put(url, headers=headers, data=json_data) as response:
                        response.raise_for_status()
                        return await response.json()
            
            else:
                # Fallback to sync requests
                response = self._sync_client.put(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            raise APIClientError(f"PUT request failed: {str(e)}") from e
    
    # Sync methods for compatibility with existing STDIO implementation
    
    def get_sync(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make synchronous GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        if REQUESTS_AVAILABLE:
            url = self._build_url(endpoint)
            headers = self.get_headers()
            
            try:
                response = self._sync_client.get(url, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise APIClientError(f"Sync GET request failed: {str(e)}") from e
        else:
            # Run async version in sync context
            return asyncio.run(self.get(endpoint, params))
    
    def post_sync(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make synchronous POST request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        if REQUESTS_AVAILABLE:
            url = self._build_url(endpoint)
            headers = self.get_headers()
            
            try:
                response = self._sync_client.post(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise APIClientError(f"Sync POST request failed: {str(e)}") from e
        else:
            # Run async version in sync context
            return asyncio.run(self.post(endpoint, data))
    
    def put_sync(self, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make synchronous PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        if REQUESTS_AVAILABLE:
            url = self._build_url(endpoint)
            headers = self.get_headers()
            
            try:
                response = self._sync_client.put(url, headers=headers, json=data)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise APIClientError(f"Sync PUT request failed: {str(e)}") from e
        else:
            # Run async version in sync context
            return asyncio.run(self.put(endpoint, data))
    
    async def close(self):
        """Close async client connections."""
        if self._client_type == "httpx" and self._async_client:
            await self._async_client.aclose()
    
    def close_sync(self):
        """Close sync client connections."""
        if self._client_type == "httpx" and self._sync_client:
            self._sync_client.close()
        elif self._client_type == "requests" and self._sync_client:
            self._sync_client.close()
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.close_sync()
        except:
            pass