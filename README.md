# SplitMind MCP Agent Communication Server (Redis Edition)

A persistent, multi-project MCP server that enables real-time communication between AI agents working on parallel tasks in SplitMind. Built with Docker and Redis for reliability and scalability.

## Key Features

- **Multi-Project Support**: Isolated namespaces for different projects
- **Persistent State**: Redis backend survives restarts and crashes
- **Todo List Management**: Each agent maintains its own task breakdown
- **Automatic Cleanup**: Dead agents are detected and cleaned up
- **Docker Deployment**: Easy setup and deployment
- **Real-time Monitoring**: Optional Redis Commander UI

## Architecture

```
Docker Network: splitmind-network
├── MCP Server Container (port 5000)
│   ├── Handles all agent communication
│   ├── Manages heartbeats and cleanup
│   └── Connects to Redis
│
├── Redis Container (port 6379)
│   ├── Persistent data storage
│   ├── Project namespacing
│   └── Append-only file for durability
│
└── Redis Commander (port 8081) [Optional]
    └── Web UI for monitoring

Redis Data Structure:
project:{project_id}:
├── agents          # Hash of active agents
├── heartbeat:{id}  # Agent heartbeat timestamps
├── locks           # File locks by agents
├── interfaces      # Shared type definitions
├── todos:{id}      # Agent todo lists
├── messages:{id}   # Message queues
└── recent_changes  # List of recent file changes
```

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository>
cd splitmind-mcp-server

# Make entrypoint executable
chmod +x entrypoint.sh
```

### 2. Start the Services

```bash
# Start MCP server and Redis
docker-compose up -d

# With monitoring UI
docker-compose --profile debug up -d

# View logs
docker-compose logs -f mcp-server
```

### 3. Configure Claude Code

Each Claude Code agent needs to know about the MCP server. Add to the agent's configuration:

```json
{
  "mcpServers": {
    "splitmind-agent-comm": {
      "command": "docker",
      "args": ["exec", "-i", "splitmind-mcp-server", "python", "mcp_server_redis.py"]
    }
  }
}
```

Or set via environment when spawning agents.

## Usage in SplitMind

### Orchestrator Integration

```python
# The orchestrator doesn't manage the MCP server
# It just tells agents how to connect

def generate_agent_prompt(task, project_id):
    session_name = f"task-{task['task_id']}"
    
    return f"""
Your task: {task['description']}

IMPORTANT - Agent Communication Setup:
1. First, register yourself:
   register_agent("{project_id}", "{session_name}", "{task['task_id']}", "{task['branch']}", "{task['description']}")

2. Create your todo list:
   add_todo("{project_id}", "{session_name}", "Research best practices", 1)
   add_todo("{project_id}", "{session_name}", "Implement core functionality", 1)
   add_todo("{project_id}", "{session_name}", "Write tests", 2)

3. Update todos as you progress:
   update_todo("{project_id}", "{session_name}", "todo-xxx", "in_progress")
   update_todo("{project_id}", "{session_name}", "todo-xxx", "completed")

4. Coordinate with others:
   - See all todos: get_all_todos("{project_id}")
   - Check active agents: list_active_agents("{project_id}")
   - Query specific agent: query_agent("{project_id}", "{session_name}", "target-session", "type", "question")

5. Send heartbeat every 30-60 seconds:
   heartbeat("{project_id}", "{session_name}")

6. When done:
   unregister_agent("{project_id}", "{session_name}")
"""
```

## MCP Tools Reference

### Core Agent Management

#### `register_agent(project_id, session_name, task_id, branch, description)`
Register when starting work. Creates empty todo list.

#### `heartbeat(project_id, session_name)`
Keep-alive signal. Call every 30-60 seconds or agent will be cleaned up.

#### `unregister_agent(project_id, session_name)`
Clean exit. Shows todo completion summary.

### Todo List Management

#### `add_todo(project_id, session_name, todo_item, priority)`
Add item to your task breakdown.
- priority: 1=high, 2=medium, 3=low

#### `update_todo(project_id, session_name, todo_id, status)`
Update todo status.
- status: pending, in_progress, completed, blocked

#### `get_my_todos(project_id, session_name)`
Get your own todo list with all details.

#### `get_all_todos(project_id)`
See all agents' todos and progress. Useful for coordination.

### Communication

#### `query_agent(project_id, from_session, to_session, query_type, query)`
Ask another agent a question. Types: interface, help, status, etc.

#### `check_messages(project_id, session_name)`
Check your message queue. Clears after reading.

#### `respond_to_query(project_id, from_session, to_session, message_id, response)`
Reply to a query.

#### `broadcast_message(project_id, session_name, message_type, content)`
Send to all agents in project.

### File Coordination

#### `announce_file_change(project_id, session_name, file_path, change_type, description)`
Lock a file before modifying. Prevents conflicts.

#### `release_file_lock(project_id, session_name, file_path)`
Release lock after changes complete.

#### `get_recent_changes(project_id, limit)`
See recent file modifications across project.

### Shared Definitions

#### `register_interface(project_id, session_name, interface_name, definition, file_path)`
Share TypeScript interfaces, types, etc.

#### `query_interface(project_id, interface_name)`
Get interface definition.

#### `list_interfaces(project_id)`
See all registered interfaces.

## Example Agent Workflow

```python
# 1. Register and setup
register_agent("ecommerce-v2", "task-auth-001", "001", "feature/auth", "Build authentication system")

# 2. Create todo list
add_todo("ecommerce-v2", "task-auth-001", "Research JWT best practices", 1)
add_todo("ecommerce-v2", "task-auth-001", "Create User model", 1)
add_todo("ecommerce-v2", "task-auth-001", "Implement login endpoint", 1)
add_todo("ecommerce-v2", "task-auth-001", "Add password hashing", 2)
add_todo("ecommerce-v2", "task-auth-001", "Write auth tests", 2)

# 3. Start working
update_todo("ecommerce-v2", "task-auth-001", "todo-123.456", "in_progress")

# 4. Check who else is working
agents = list_active_agents("ecommerce-v2")
# See task-profile-002 is also active

# 5. Create and share interface
announce_file_change("ecommerce-v2", "task-auth-001", "src/types/user.ts", "create", "Creating User interface")
# ... create file ...
register_interface("ecommerce-v2", "task-auth-001", "User", "interface User { id: string; email: string; role: string; }")
release_file_lock("ecommerce-v2", "task-auth-001", "src/types/user.ts")

# 6. Complete todo
update_todo("ecommerce-v2", "task-auth-001", "todo-123.456", "completed")

# 7. Heartbeat (every 30-60 seconds)
heartbeat("ecommerce-v2", "task-auth-001")

# 8. Check messages periodically
messages = check_messages("ecommerce-v2", "task-auth-001")
# Respond if needed

# 9. When done
unregister_agent("ecommerce-v2", "task-auth-001")
# Shows: "Completed 4/5 todos"
```

## Monitoring

### Redis Commander (Web UI)

Access at http://localhost:8081 when running with debug profile.

View:
- Active agents by project
- Current file locks
- Todo lists and progress
- Message queues
- Shared interfaces

### Docker Logs

```bash
# All logs
docker-compose logs -f

# Just MCP server
docker-compose logs -f mcp-server

# Just Redis
docker-compose logs -f redis
```

### Direct Redis Access

```bash
# Connect to Redis CLI
docker exec -it splitmind-redis redis-cli

# View all projects
KEYS project:*

# View agents in a project
HGETALL project:myproject:agents

# View an agent's todos
LRANGE project:myproject:todos:task-001 0 -1

# Monitor real-time commands
MONITOR
```

## Production Deployment

### Security Considerations

1. **Network Isolation**: Keep Redis internal
   ```yaml
   # Remove Redis port exposure
   redis:
     # ports:
     #   - "6379:6379"
   ```

2. **Authentication**: Add Redis password
   ```yaml
   environment:
     - REDIS_URL=redis://:your-password@redis:6379
   ```

3. **Resource Limits**: Set memory constraints
   ```yaml
   services:
     mcp-server:
       mem_limit: 512m
     redis:
       mem_limit: 1g
   ```

### Scaling

For large deployments:
- Use Redis Cluster for horizontal scaling
- Add connection pooling
- Implement request rate limiting
- Consider message queue alternatives (RabbitMQ, Kafka)

### Backup

Redis data is persisted in the `redis-data` volume:

```bash
# Backup
docker run --rm -v splitmind-mcp-server_redis-data:/data -v $(pwd):/backup alpine tar czf /backup/redis-backup.tar.gz -C /data .

# Restore
docker run --rm -v splitmind-mcp-server_redis-data:/data -v $(pwd):/backup alpine tar xzf /backup/redis-backup.tar.gz -C /data
```

## Troubleshooting

### Agent Not Registering
- Check MCP server is running: `docker ps`
- Verify network connectivity
- Check logs: `docker-compose logs mcp-server`

### Heartbeat Timeouts
- Ensure agents call `heartbeat()` every 30-60 seconds
- Check network latency
- Increase HEARTBEAT_TIMEOUT if needed

### Redis Connection Issues
- Verify Redis is healthy: `docker-compose ps`
- Check Redis logs: `docker-compose logs redis`
- Test connection: `docker exec splitmind-redis redis-cli ping`

### Memory Issues
- Monitor Redis memory: `docker exec splitmind-redis redis-cli info memory`
- Adjust maxmemory in redis.conf
- Clear old data: `get_recent_changes` with limit

## Development

### Running Locally (Without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server redis.conf

# Run MCP server
REDIS_URL=redis://localhost:6379 python mcp_server_redis.py
```

### Adding New Tools

1. Add tool method in `_setup_tools()`
2. Update heartbeat if it modifies state
3. Add Redis operations using project namespacing
4. Update README documentation

## License

MIT License - See LICENSE file for details