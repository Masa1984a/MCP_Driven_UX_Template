#!/usr/bin/env python3
"""Test script for MCP server endpoints."""

import requests
import json

# Configuration
BASE_URL = "https://mcp-server-883360737972.asia-northeast1.run.app"
API_KEY = "mcp-auth-e91c006a-c876-4dd4-bc7a-27aebcb85cbf"

def test_health():
    """Test health endpoint."""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_sse_connection():
    """Test SSE connection."""
    print("Testing SSE connection...")
    url = f"{BASE_URL}/sse?api_key={API_KEY}"
    response = requests.get(url, stream=True)
    print(f"Status: {response.status_code}")
    print(f"Headers: {response.headers}")
    
    # Read first few lines
    count = 0
    for line in response.iter_lines():
        if line:
            print(f"SSE: {line.decode('utf-8')}")
            count += 1
            if count > 5:
                break
    response.close()
    print()

def test_message_endpoint():
    """Test message endpoint - first establish connection to get real ID."""
    print("Testing message endpoint...")
    
    # Step 1: Get a real connection ID from SSE endpoint
    print("Step 1: Establishing SSE connection to get connection ID...")
    url = f"{BASE_URL}/sse?api_key={API_KEY}"
    response = requests.get(url, stream=True)
    
    if response.status_code != 200:
        print(f"Failed to establish SSE connection: {response.status_code}")
        return
    
    connection_id = None
    # Read the first welcome message to get connection ID
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith('data: '):
                try:
                    data = json.loads(line_str[6:])  # Remove 'data: ' prefix
                    if data.get("type") == "welcome":
                        connection_id = data.get("connection_id")
                        print(f"Got connection ID: {connection_id}")
                        break
                except json.JSONDecodeError:
                    continue
    
    response.close()
    
    if not connection_id:
        print("Failed to get connection ID from SSE")
        return
    
    # Step 2: Test message endpoint with real connection ID
    print(f"Step 2: Testing message endpoint with connection ID: {connection_id}")
    
    # Test initialize message
    message = {
        "type": "initialize",
        "id": "init-1",
        "params": {}
    }
    
    url = f"{BASE_URL}/message/{connection_id}?api_key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    response = requests.post(url, json=message, headers=headers)
    print(f"Initialize - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()

if __name__ == "__main__":
    test_health()
    test_sse_connection()
    test_message_endpoint()