# Claude Code MCP Setup Guide

## Installing A2AMCP in Claude Code

### Method 1: Using Claude Code CLI (Recommended)

```bash
# Add the A2AMCP server to Claude Code
claude mcp add splitmind-a2amcp \
  -e REDIS_URL=redis://localhost:6379 \
  -- docker exec -i splitmind-mcp-server python /app/mcp-server-redis.py
```

### Method 2: Direct Configuration

Edit your Claude Code configuration:

```bash
# Open Claude Code config
claude config edit
```

Add the following to the `mcpServers` section:

```json
{
  "mcpServers": {
    "splitmind-a2amcp": {
      "command": "docker",
      "args": ["exec", "-i", "splitmind-mcp-server", "python", "/app/mcp-server-redis.py"],
      "env": {
        "REDIS_URL": "redis://redis:6379"
      }
    }
  }
}
```

## Generic Use Cases

A2AMCP can be used for any multi-agent coordination scenario:

### 1. **Microservices Development**
```bash
# Coordinate multiple agents building different services
claude mcp add a2amcp-microservices \
  -e PROJECT_ID=my-microservices \
  -- docker exec -i splitmind-mcp-server python /app/mcp-server-redis.py
```

### 2. **Full-Stack Applications**
```bash
# Frontend and backend agents working together
claude mcp add a2amcp-fullstack \
  -e PROJECT_ID=my-app \
  -- docker exec -i splitmind-mcp-server python /app/mcp-server-redis.py
```

### 3. **Documentation Projects**
```bash
# Multiple agents creating interconnected docs
claude mcp add a2amcp-docs \
  -e PROJECT_ID=documentation \
  -- docker exec -i splitmind-mcp-server python /app/mcp-server-redis.py
```

## Verifying Installation

After adding the MCP server, verify it's working:

```bash
# List all MCP servers
claude mcp list

# Test the A2AMCP server
claude mcp test splitmind-a2amcp
```

## Usage in Claude Code

Once installed, you can use A2AMCP tools in your prompts:

```
@splitmind-a2amcp register_agent project_id="my-project" session_name="frontend-agent" task_id="TASK-001" branch="feature/ui" description="Building user interface"

@splitmind-a2amcp get_active_agents project_id="my-project"

@splitmind-a2amcp send_message project_id="my-project" from_session="frontend-agent" to_session="backend-agent" message="What's the user API endpoint?"

@splitmind-a2amcp mark_task_completed project_id="my-project" session_name="frontend-agent" task_id="TASK-001"
```

## Environment Variables

You can customize the server behavior with environment variables:

```bash
claude mcp add splitmind-a2amcp \
  -e REDIS_URL=redis://localhost:6379 \
  -e LOG_LEVEL=DEBUG \
  -e HEARTBEAT_TIMEOUT=300 \
  -- docker exec -i splitmind-mcp-server python /app/mcp-server-redis.py
```

## Troubleshooting

### Server not responding
```bash
# Check if Docker containers are running
docker ps | grep splitmind

# View server logs
docker logs splitmind-mcp-server

# Test Redis connection
docker exec splitmind-redis redis-cli ping
```

### Permission issues
```bash
# Ensure Docker is accessible
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Port conflicts
If port 6379 is already in use, update the Redis URL:
```bash
claude mcp add splitmind-a2amcp \
  -e REDIS_URL=redis://localhost:6380 \
  -- docker exec -i splitmind-mcp-server python /app/mcp-server-redis.py
```