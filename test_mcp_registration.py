#!/usr/bin/env python3
"""Test MCP tool registration patterns"""

from mcp.server import Server
from mcp.types import Tool
import inspect

# Create a server instance
server = Server("test-server")

# Check if we can create Tool objects
print("Tool class:")
print(f"  - Tool type: {Tool}")
print(f"  - Tool attributes: {[attr for attr in dir(Tool) if not attr.startswith('_')]}")

# Check server's request_handlers
print("\nServer request handlers:")
print(f"  - Type: {type(server.request_handlers)}")
print(f"  - Methods: {[m for m in dir(server.request_handlers) if not m.startswith('_')]}")

# Look for tool-related attributes
print("\nChecking for tool storage:")
for attr in dir(server):
    value = getattr(server, attr)
    if 'tool' in attr.lower() or (hasattr(value, '__name__') and 'tool' in str(value).lower()):
        print(f"  - {attr}: {type(value)}")