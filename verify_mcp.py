#!/usr/bin/env python3
"""
Verify A2AMCP MCP server is accessible and working
"""
import json
import subprocess
import sys

def test_mcp_connection():
    """Test that MCP server responds correctly"""
    print("Testing A2AMCP MCP Server Connection...")
    print("=" * 50)
    
    # Test health endpoint
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:5050/health"],
            capture_output=True,
            text=True
        )
        health = json.loads(result.stdout)
        print(f"✓ Health Check: {health['status']}")
        print(f"  - Service: {health['service']}")
        print(f"  - Redis: {health['redis']}")
    except Exception as e:
        print(f"✗ Health Check Failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("MCP Server Configuration for Claude Desktop:")
    print("=" * 50)
    
    config = {
        "mcpServers": {
            "splitmind-a2amcp": {
                "command": "docker",
                "args": [
                    "exec",
                    "-i",
                    "splitmind-mcp-server",
                    "python",
                    "/app/mcp-server-redis.py"
                ],
                "env": {
                    "REDIS_URL": "redis://redis:6379"
                }
            }
        }
    }
    
    print(json.dumps(config, indent=2))
    
    print("\n" + "=" * 50)
    print("Available A2AMCP Tools (when connected):")
    print("=" * 50)
    
    tools = [
        "register_agent - Register an agent for a project",
        "list_active_agents - List all active agents",
        "query_agent - Send query to another agent",
        "check_messages - Check and retrieve messages",
        "announce_file_change - Lock a file before editing",
        "release_file_lock - Release file lock after editing",
        "get_recent_changes - Get recent file changes",
        "register_interface - Share a type/interface definition",
        "...and 9 more tools"
    ]
    
    for tool in tools:
        print(f"  • {tool}")
    
    print("\n" + "=" * 50)
    print("Status: ✓ Server is running and ready!")
    print("=" * 50)
    print("\nNOTE: If agents cannot see 'mcp__splitmind-a2amcp__' tools:")
    print("1. Restart Claude Desktop to reload MCP configuration")
    print("2. Check ~/Library/Application Support/Claude/claude_desktop_config.json")
    print("3. Ensure Docker is running: docker ps | grep splitmind")
    
    return True

if __name__ == "__main__":
    success = test_mcp_connection()
    sys.exit(0 if success else 1)