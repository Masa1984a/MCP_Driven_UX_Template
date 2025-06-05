#!/usr/bin/env python3
"""Test script for MCP-compliant SSE + Messages implementation."""

import requests
import json
import asyncio
import aiohttp
import uuid
from typing import Optional

# Configuration
BASE_URL = "https://mcp-server-883360737972.asia-northeast1.run.app"
API_KEY = "mcp-auth-e91c006a-c876-4dd4-bc7a-27aebcb85cbf"

class MCPStandardTester:
    """Test MCP-compliant implementation."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.session_id = None
        self.messages_endpoint = None
    
    def test_health(self):
        """Test health endpoint."""
        print("=== Testing health endpoint ===")
        response = requests.get(f"{self.base_url}/health")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()
    
    async def test_sse_endpoint_info(self):
        """Test SSE endpoint for initial endpoint information."""
        print("=== Testing SSE endpoint (MCP standard) ===")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache"
        }
        
        url = f"{self.base_url}/sse"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    print(f"Status: {response.status}")
                    print(f"Headers: {dict(response.headers)}")
                    
                    if response.status != 200:
                        text = await response.text()
                        print(f"Error: {text}")
                        return False
                    
                    # Read SSE events with detailed parsing
                    event_count = 0
                    current_event = None
                    current_data = None
                    
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        
                        if line_str:
                            print(f"SSE: {line_str}")
                            
                            # Parse SSE fields
                            if line_str.startswith('event: '):
                                current_event = line_str[7:]
                                print(f"✓ Event type: {current_event}")
                            elif line_str.startswith('data: '):
                                current_data = line_str[6:]
                                print(f"✓ Data: {current_data}")
                                
                                # Handle endpoint event
                                if current_event == 'endpoint':
                                    if current_data.startswith('/messages?session_id='):
                                        session_id = current_data.split('session_id=')[1]
                                        self.session_id = session_id
                                        self.messages_endpoint = f"{self.base_url}/messages?session_id={session_id}"
                                        print(f"✓ Got session ID: {session_id}")
                                        print(f"✓ Messages endpoint: {self.messages_endpoint}")
                                        
                                # Handle message event  
                                elif current_event == 'message':
                                    try:
                                        message_data = json.loads(current_data)
                                        print(f"✓ Message data: {json.dumps(message_data, indent=2)}")
                                        if self.session_id:
                                            break  # We have what we need
                                    except json.JSONDecodeError as e:
                                        print(f"✗ JSON decode error: {e}")
                            elif line_str.startswith(': '):
                                print(f"✓ Keep-alive: {line_str}")
                        
                        event_count += 1
                        if event_count > 20:  # Prevent infinite loop
                            break
                    
                    return self.session_id is not None
                    
        except Exception as e:
            print(f"SSE connection error: {e}")
            return False
    
    async def test_messages_endpoint(self):
        """Test messages endpoint with MCP JSON-RPC."""
        if not self.session_id or not self.messages_endpoint:
            print("❌ No session ID available. Run SSE test first.")
            return
        
        print("=== Testing Messages endpoint (MCP JSON-RPC) ===")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Initialize
        print("Test 1: Initialize")
        init_message = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "initialize",
            "params": {
                "protocolVersion": "1.0",
                "clientName": "MCP Test Client",
                "clientVersion": "1.0.0"
            }
        }
        
        response = requests.post(
            self.messages_endpoint,
            headers=headers,
            json=init_message
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()
        
        # Test 2: List tools
        print("Test 2: List tools")
        list_tools_message = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/list",
            "params": {}
        }
        
        response = requests.post(
            self.messages_endpoint,
            headers=headers,
            json=list_tools_message
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()
        
        # Test 3: Tool call (search)
        print("Test 3: Tool call (search)")
        tool_call_message = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "search",
                "arguments": {
                    "query": "test ticket"
                }
            }
        }
        
        response = requests.post(
            self.messages_endpoint,
            headers=headers,
            json=tool_call_message
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()
        
        # Test 4: Ping
        print("Test 4: Ping")
        ping_message = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "ping",
            "params": {}
        }
        
        response = requests.post(
            self.messages_endpoint,
            headers=headers,
            json=ping_message
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()
    
    def test_query_param_auth(self):
        """Test backward compatibility with query parameter auth."""
        print("=== Testing query parameter auth (backward compatibility) ===")
        
        url = f"{self.base_url}/sse?api_key={self.api_key}"
        
        response = requests.get(url, stream=True)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            count = 0
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"SSE: {line_str}")
                    count += 1
                    if count > 5:
                        break
        else:
            print(f"Error: {response.text}")
        
        response.close()
        print()

async def main():
    """Run all tests."""
    tester = MCPStandardTester(BASE_URL, API_KEY)
    
    # Test health
    tester.test_health()
    
    # Test SSE endpoint with Bearer token
    success = await tester.test_sse_endpoint_info()
    
    if success:
        # Test messages endpoint
        await tester.test_messages_endpoint()
    
    # Test backward compatibility
    tester.test_query_param_auth()
    
    print("=== Test Summary ===")
    if tester.session_id:
        print("✅ MCP-compliant SSE implementation working")
        print(f"✅ Session ID: {tester.session_id}")
        print(f"✅ Messages endpoint: {tester.messages_endpoint}")
    else:
        print("❌ MCP-compliant SSE implementation not working")

if __name__ == "__main__":
    asyncio.run(main())