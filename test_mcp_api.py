#!/usr/bin/env python3
"""Test MCP API to understand correct tool registration"""

from mcp.server import Server

# Create a server instance
server = Server("test-server")

# Check available methods
print("Server methods:")
for method in dir(server):
    if not method.startswith('_'):
        print(f"  - {method}")

# Check for tool-related methods
tool_methods = [m for m in dir(server) if 'tool' in m.lower()]
print(f"\nTool-related methods: {tool_methods}")