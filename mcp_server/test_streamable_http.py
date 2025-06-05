#!/usr/bin/env python3
"""
Streamable HTTP MCP Server Test Script

Tests the new Streamable HTTP implementation with MCP Inspector compatibility
and backward compatibility with existing SSE endpoints.
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any, Optional
import aiohttp
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "https://mcp-server-883360737972.asia-northeast1.run.app"
API_KEY = "test-api-key-12345"
TIMEOUT = 30

class StreamableHTTPTester:
    """Test client for Streamable HTTP MCP implementation."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session_id: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test health check endpoint."""
        logger.info("Testing health check endpoint...")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Health check passed: {data}")
                    return True
                else:
                    logger.error(f"Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return False
    
    async def test_initialize_request(self) -> bool:
        """Test initialize request (creates session)."""
        logger.info("Testing initialize request...")
        
        try:
            # Prepare initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "Test Client",
                        "version": "1.0.0"
                    }
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json, text/event-stream"  # Required by spec
            }
            
            # Send initialize request
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=init_request,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    # Extract session ID from header
                    self.session_id = response.headers.get("Mcp-Session-Id")
                    
                    if self.session_id:
                        logger.info(f"Initialize successful, session ID: {self.session_id}")
                        
                        # Check response
                        data = await response.json()
                        if data.get("jsonrpc") == "2.0" and "result" in data:
                            logger.info(f"Initialize response valid: {data}")
                            return True
                        else:
                            logger.error(f"Invalid initialize response: {data}")
                            return False
                    else:
                        logger.error("No session ID in response headers")
                        return False
                else:
                    logger.error(f"Initialize failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Initialize error: {e}")
            return False
    
    async def test_sse_stream(self) -> bool:
        """Test SSE stream establishment."""
        if not self.session_id:
            logger.error("No session ID available for SSE test")
            return False
        
        logger.info("Testing SSE stream establishment...")
        
        try:
            headers = {
                "Mcp-Session-Id": self.session_id,
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "text/event-stream"  # GET requires only text/event-stream
            }
            
            # Test SSE stream (just check if connection is established)
            async with self.session.get(
                f"{self.base_url}/mcp",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    # Read first few SSE messages
                    messages_received = 0
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data:'):
                            logger.info(f"SSE message: {line}")
                            messages_received += 1
                            
                            # Check for endpoint event
                            if 'endpoint' in line:
                                logger.info("Endpoint event received")
                            
                            # Break after receiving a few messages
                            if messages_received >= 3:
                                break
                    
                    if messages_received > 0:
                        logger.info(f"SSE stream test passed, received {messages_received} messages")
                        return True
                    else:
                        logger.error("No SSE messages received")
                        return False
                else:
                    logger.error(f"SSE stream failed: {response.status}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.info("SSE stream timeout (expected behavior)")
            return True  # Timeout is expected for SSE streams
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            return False
    
    async def test_tools_list(self) -> bool:
        """Test tools/list request."""
        if not self.session_id:
            logger.error("No session ID available for tools list test")
            return False
        
        logger.info("Testing tools/list request...")
        
        try:
            # Prepare tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json, text/event-stream"  # Required by spec
            }
            
            # Send tools/list request
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=tools_request,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("jsonrpc") == "2.0" and "result" in data:
                        tools = data["result"].get("tools", [])
                        logger.info(f"Tools list successful, {len(tools)} tools available")
                        for tool in tools:
                            logger.info(f"  Tool: {tool.get('name')} - {tool.get('description')}")
                        return True
                    else:
                        logger.error(f"Invalid tools/list response: {data}")
                        return False
                else:
                    logger.error(f"Tools list failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Tools list error: {e}")
            return False
    
    async def test_search_tool(self) -> bool:
        """Test search tool execution."""
        if not self.session_id:
            logger.error("No session ID available for search tool test")
            return False
        
        logger.info("Testing search tool execution...")
        
        try:
            # Prepare tools/call request for search
            search_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "search",
                    "arguments": {
                        "query": "test search query"
                    }
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json, text/event-stream"  # Required by spec
            }
            
            # Send search tool request
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=search_request,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    if data.get("jsonrpc") == "2.0" and "result" in data:
                        result = data["result"]
                        logger.info(f"Search tool successful: {result}")
                        return True
                    else:
                        logger.error(f"Invalid search tool response: {data}")
                        return False
                else:
                    logger.error(f"Search tool failed: {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error response: {error_text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Search tool error: {e}")
            return False
    
    async def test_notification_202_response(self) -> bool:
        """Test that notifications return 202 Accepted as per spec."""
        if not self.session_id:
            logger.error("No session ID available for notification test")
            return False
        
        logger.info("Testing notification 202 Accepted response...")
        
        try:
            # Send a notification (cancellation example)
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/cancelled",
                "params": {
                    "requestId": "test-request-123",
                    "reason": "Test cancellation"
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json, text/event-stream"
            }
            
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=notification,
                headers=headers
            ) as response:
                
                if response.status == 202:
                    logger.info("Notification 202 Accepted test passed")
                    return True
                else:
                    logger.error(f"Notification test failed: expected 202, got {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Notification test error: {e}")
            return False
    
    async def test_accept_header_validation(self) -> bool:
        """Test Accept header validation as per spec."""
        if not self.session_id:
            logger.error("No session ID available for Accept header test")
            return False
        
        logger.info("Testing Accept header validation...")
        
        try:
            # Test with invalid Accept header
            tools_request = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "tools/list",
                "params": {}
            }
            
            headers = {
                "Content-Type": "application/json",
                "Mcp-Session-Id": self.session_id,
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"  # Missing text/event-stream
            }
            
            async with self.session.post(
                f"{self.base_url}/mcp",
                json=tools_request,
                headers=headers
            ) as response:
                
                if response.status == 400:
                    data = await response.json()
                    if "Accept header" in data.get("error", {}).get("message", ""):
                        logger.info("Accept header validation test passed")
                        return True
                    else:
                        logger.error(f"Accept header test failed: wrong error message: {data}")
                        return False
                else:
                    logger.error(f"Accept header test failed: expected 400, got {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Accept header test error: {e}")
            return False
    
    async def test_backward_compatibility(self) -> bool:
        """Test backward compatibility with existing SSE endpoints."""
        logger.info("Testing backward compatibility with SSE endpoints...")
        
        try:
            # Test legacy SSE endpoint
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with self.session.get(
                f"{self.base_url}/sse",
                headers=headers
            ) as response:
                
                if response.status == 200:
                    # Read first SSE message
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data:'):
                            logger.info(f"Legacy SSE message: {line}")
                            break
                    
                    logger.info("Backward compatibility test passed")
                    return True
                else:
                    logger.error(f"Legacy SSE test failed: {response.status}")
                    return False
                    
        except asyncio.TimeoutError:
            logger.info("Legacy SSE timeout (expected behavior)")
            return True
        except Exception as e:
            logger.error(f"Backward compatibility error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all tests and return results."""
        results = {}
        
        # Test 1: Health check
        results["health_check"] = await self.test_health_check()
        
        # Test 2: Initialize request (creates session)
        results["initialize"] = await self.test_initialize_request()
        
        # Test 3: SSE stream establishment
        if results["initialize"]:
            results["sse_stream"] = await self.test_sse_stream()
        else:
            results["sse_stream"] = False
        
        # Test 4: Tools list
        if results["initialize"]:
            results["tools_list"] = await self.test_tools_list()
        else:
            results["tools_list"] = False
        
        # Test 5: Search tool execution
        if results["initialize"]:
            results["search_tool"] = await self.test_search_tool()
        else:
            results["search_tool"] = False
        
        # Test 6: Notification 202 Accepted response
        if results["initialize"]:
            results["notification_202"] = await self.test_notification_202_response()
        else:
            results["notification_202"] = False
        
        # Test 7: Accept header validation
        if results["initialize"]:
            results["accept_header_validation"] = await self.test_accept_header_validation()
        else:
            results["accept_header_validation"] = False
        
        # Test 8: Backward compatibility
        results["backward_compatibility"] = await self.test_backward_compatibility()
        
        return results


async def main():
    """Main test function."""
    logger.info("Starting Streamable HTTP MCP Server Tests")
    logger.info(f"Base URL: {BASE_URL}")
    
    async with StreamableHTTPTester(BASE_URL, API_KEY) as tester:
        results = await tester.run_all_tests()
    
    # Print results
    print("\n" + "="*60)
    print("STREAMABLE HTTP MCP SERVER TEST RESULTS")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25}: {status}")
    
    print("-"*60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! Streamable HTTP implementation is working correctly.")
        return 0
    else:
        print(f"\n❌ {total_tests - passed_tests} test(s) failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest execution error: {e}")
        sys.exit(1)