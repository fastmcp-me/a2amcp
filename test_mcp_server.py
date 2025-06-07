#!/usr/bin/env python3
"""
Test script for A2AMCP Server
Simulates MCP client communication via STDIO
"""

import asyncio
import json
import sys
from typing import Dict, Any

async def send_request(request: Dict[str, Any]):
    """Send a JSON-RPC request via STDIO"""
    print(json.dumps(request), flush=True)

async def read_response():
    """Read a JSON-RPC response from STDIO"""
    line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
    if line:
        return json.loads(line.strip())
    return None

async def test_mcp_communication():
    """Test MCP server communication"""
    
    # Initialize connection
    print("Testing MCP Server Communication...", file=sys.stderr)
    
    # Test 1: List available tools
    await send_request({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
    
    response = await read_response()
    if response:
        print(f"Available tools: {len(response.get('result', {}).get('tools', []))}", file=sys.stderr)
    
    # Test 2: Register an agent
    await send_request({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "register_agent",
            "arguments": {
                "project_id": "test-project",
                "session_name": "test-agent-1",
                "task_id": "TASK-123",
                "branch": "feature/test",
                "description": "Test agent for validation"
            }
        },
        "id": 2
    })
    
    response = await read_response()
    if response:
        print(f"Agent registration: {response.get('result')}", file=sys.stderr)
    
    # Test 3: Send a message
    await send_request({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "send_message",
            "arguments": {
                "project_id": "test-project",
                "from_session": "test-agent-1",
                "to_session": "test-agent-2",
                "message": "Hello from test agent 1",
                "message_type": "query"
            }
        },
        "id": 3
    })
    
    response = await read_response()
    if response:
        print(f"Message sent: {response.get('result')}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(test_mcp_communication())