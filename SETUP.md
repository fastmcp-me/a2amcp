# A2AMCP Server Setup Guide

## Overview
The A2AMCP (Agent-to-Agent Model Context Protocol) server enables communication between AI agents working on the SplitMind platform. It uses Redis for state management and communicates via MCP's STDIO protocol.

## Running the Server

1. **Start the Docker containers:**
   ```bash
   docker-compose up -d
   ```

2. **Verify containers are running:**
   ```bash
   docker ps | grep splitmind
   ```

   You should see:
   - `splitmind-mcp-server` - The MCP server container
   - `splitmind-redis` - Redis for state storage

3. **Check server logs:**
   ```bash
   docker logs splitmind-mcp-server
   ```

## Configuring Claude Desktop

Add the following to your Claude Desktop MCP configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
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
```

## Available MCP Tools

### Agent Management
- **register_agent** - Register an agent for a project
- **unregister_agent** - Unregister an agent when done
- **get_active_agents** - List all active agents
- **heartbeat** - Keep agent alive

### Communication
- **send_message** - Send message to another agent
- **get_messages** - Retrieve pending messages

### Task Management
- **update_todo_list** - Update agent's todo list
- **get_todo_list** - Get current todos

### File Coordination
- **register_file_change** - Lock a file for editing
- **release_file** - Release file lock
- **check_file_conflicts** - Check for file conflicts

### Task Completion
- **mark_task_completed** - Signal task completion to orchestrator

## Testing

Run the test script to verify all endpoints:
```bash
python test_endpoints.py
```

## Ports
- **5050** - MCP server (mapped from internal 5000)
- **6379** - Redis
- **8081** - Redis Commander UI (optional, with `--profile debug`)

## Troubleshooting

1. **Server keeps restarting:**
   - This is normal for STDIO-based MCP servers
   - The server only runs when Claude connects to it

2. **Connection issues:**
   - Ensure Docker is running
   - Check Redis is healthy: `docker exec splitmind-redis redis-cli ping`
   - Verify port 5050 is not in use

3. **View Redis data:**
   ```bash
   docker-compose --profile debug up -d
   ```
   Then open http://localhost:8081 for Redis Commander UI