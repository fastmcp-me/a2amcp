# How SplitMind MCP Agent Communication Works

## System Architecture

```
┌─────────────────────────────────────────────────┐
│                  Your Machine                    │
│                                                  │
│  ┌─────────────────┐      ┌─────────────────┐  │
│  │  Orchestrator   │      │  Docker Host     │  │
│  │  (Python)       │      │                  │  │
│  │                 │      │  ┌─────────────┐ │  │
│  │  - Spawns       │      │  │ MCP Server  │ │  │
│  │    agents       │      │  │ Container   │ │  │
│  │  - Creates      │      │  │ Port: 5000  │ │  │
│  │    prompts      │      │  └──────┬──────┘ │  │
│  │                 │      │         │         │  │
│  └─────────────────┘      │  ┌──────┴──────┐ │  │
│                           │  │   Redis     │ │  │
│                           │  │  Container  │ │  │
│                           │  │ Port: 6379  │ │  │
│                           │  └─────────────┘ │  │
│                           └─────────────────┘  │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │          TMUX Sessions (Agents)           │  │
│  │                                           │  │
│  │  ┌────────┐┌────────┐┌────────┐┌────────┐│  │
│  │  │Agent 1 ││Agent 2 ││Agent 3 ││Agent N ││  │
│  │  │task-001││task-002││task-003││task-...││  │
│  │  └────────┘└────────┘└────────┘└────────┘│  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Step-by-Step Flow

### 1. **System Initialization**

```bash
# Developer runs quick start
./quickstart.sh

# This starts:
docker-compose up -d
```

**Result**: 
- MCP Server container starts on port 5000
- Redis container starts on port 6379
- Both are networked together

### 2. **Orchestrator Starts**

```python
# In your SplitMind orchestrator
orchestrator = Orchestrator()
orchestrator.run_tasks(project_id="ecommerce-v2", tasks=[...])
```

**The orchestrator**:
- Does NOT manage the MCP server (it's already running)
- Prepares prompts with MCP instructions
- Spawns agents in tmux sessions

### 3. **Agent Spawning**

For each task, the orchestrator:

```python
session_name = f"task-{task['task_id']}"  # e.g., "task-001"

# Creates a git worktree
worktree = create_worktree(task['branch'])

# Generates prompt with MCP instructions
prompt = generate_mcp_prompt(task, project_id, session_name)

# Spawns Claude Code in tmux
tmux new-session -d -s {session_name}
tmux send-keys "claude-code '{prompt}'"
```

### 4. **Agent Registration**

Each agent's FIRST action (from the prompt):

```python
register_agent("ecommerce-v2", "task-001", "001", "feature/auth", "Build authentication")
```

**What happens**:
1. Agent calls MCP tool → MCP Server
2. Server stores in Redis: `project:ecommerce-v2:agents:task-001`
3. Server broadcasts to other agents: "New agent joined"
4. Agent receives list of other active agents

### 5. **Todo List Creation**

Agent breaks down its task:

```python
add_todo("ecommerce-v2", "task-001", "Research JWT libraries", 1)
add_todo("ecommerce-v2", "task-001", "Create User model", 1)
add_todo("ecommerce-v2", "task-001", "Implement login endpoint", 1)
```

**Stored in Redis**: `project:ecommerce-v2:todos:task-001`

### 6. **Agent Discovery**

Agents check who else is working:

```python
# Agent task-002 starts and checks
list_active_agents("ecommerce-v2")

# Returns:
{
  "task-001": {
    "task_id": "001",
    "description": "Build authentication",
    "status": "active"
  }
}

# Check what they're doing
get_all_todos("ecommerce-v2")

# Returns everyone's todo lists and progress
```

### 7. **Inter-Agent Communication**

#### Direct Query:
```python
# Agent 2 needs information from Agent 1
query_agent(
    "ecommerce-v2", 
    "task-002",      # from
    "task-001",      # to
    "interface",     # query type
    "What's the User interface structure?"
)
```

**Flow**:
1. Message stored in Redis: `project:ecommerce-v2:messages:task-001`
2. Agent 1 checks messages periodically
3. Agent 1 responds
4. Response delivered back to Agent 2

#### Broadcast:
```python
broadcast_message(
    "ecommerce-v2",
    "task-001",
    "info",
    "Starting major refactor of auth system"
)
```

All agents see this in their message queue.

### 8. **File Coordination**

```python
# Agent 1 wants to modify a file
announce_file_change(
    "ecommerce-v2",
    "task-001",
    "src/models/user.ts",
    "create",
    "Creating User model"
)
```

**What happens**:
1. Server checks Redis: `project:ecommerce-v2:locks`
2. If no lock exists, creates one
3. If locked by another agent, returns conflict
4. Broadcasts lock notification to others

### 9. **Shared Definitions**

```python
# Agent 1 creates and shares
register_interface(
    "ecommerce-v2",
    "task-001",
    "User",
    "interface User { id: string; email: string; role: string; }"
)
```

**Stored in**: `project:ecommerce-v2:interfaces:User`

Other agents can immediately:
```python
query_interface("ecommerce-v2", "User")
# Gets the complete interface definition
```

### 10. **Heartbeat & Cleanup**

Every 30-60 seconds:
```python
heartbeat("ecommerce-v2", "task-001")
```

**MCP Server monitors**:
- If no heartbeat for 2 minutes → agent is dead
- Automatically releases file locks
- Removes from active agents
- Notifies others

### 11. **Task Completion**

```python
# Agent finishes
unregister_agent("ecommerce-v2", "task-001")
```

**Server**:
- Shows todo completion stats
- Releases all locks
- Broadcasts departure
- Cleans up message queues

## Data Flow Example

```
Time 0: Project "ecommerce-v2" starts
        └── MCP Server already running in Docker

Time 1: Agent task-001 (auth) starts
        ├── Registers with MCP
        ├── Creates 5 todos
        └── Starts working

Time 2: Agent task-002 (profile) starts
        ├── Registers with MCP
        ├── Sees task-001 is active
        ├── Checks task-001's todos
        └── Sees "Create User model" is pending

Time 3: Agent task-001 completes User model
        ├── Updates todo to "completed"
        ├── Registers interface "User"
        └── Broadcasts completion

Time 4: Agent task-002 queries
        ├── "What's the User interface?"
        └── Gets immediate response

Time 5: Both agents coordinate
        ├── task-001: "I'll do auth endpoints"
        ├── task-002: "I'll do profile endpoints"
        └── No conflicts!
```

## Redis Data Structure

```
redis:6379
└── project:ecommerce-v2:
    ├── agents                    # Hash: session -> agent info
    │   ├── task-001: {status: "active", task_id: "001", ...}
    │   └── task-002: {status: "active", task_id: "002", ...}
    │
    ├── heartbeat:task-001        # String: last heartbeat timestamp
    ├── heartbeat:task-002        # String: last heartbeat timestamp
    │
    ├── todos:task-001           # List: todo items
    │   ├── {id: "todo-1", text: "Research JWT", status: "completed"}
    │   └── {id: "todo-2", text: "Create User model", status: "completed"}
    │
    ├── todos:task-002           # List: todo items
    │   └── {id: "todo-3", text: "Design profile schema", status: "in_progress"}
    │
    ├── messages:task-001        # List: incoming messages
    ├── messages:task-002        # List: incoming messages
    │
    ├── locks                    # Hash: filepath -> lock info
    │   └── src/models/user.ts: {session: "task-001", locked_at: "..."}
    │
    ├── interfaces               # Hash: name -> definition
    │   └── User: {definition: "interface User {...}", registered_by: "task-001"}
    │
    └── recent_changes          # List: recent file modifications
```

## Key Design Principles

### 1. **Stateless Agents**
- Agents don't store state locally
- Everything is in Redis
- Can restart without losing context

### 2. **Project Isolation**
- Each project has its own namespace
- No cross-project communication
- Complete data isolation

### 3. **Eventual Consistency**
- Agents check messages periodically
- Not real-time, but near real-time
- Good enough for code development

### 4. **Failure Resilience**
- Heartbeat monitoring
- Automatic cleanup
- No orphaned locks

### 5. **Transparency**
- All agents can see all todos
- Shared interfaces visible immediately
- Progress tracking for coordination

## Why This Works

1. **No Direct Agent-to-Agent Connections**: Everything goes through the central MCP server
2. **Persistent State**: Redis keeps everything even if agents crash
3. **Simple Protocol**: Just MCP tool calls, no complex networking
4. **Observable**: Can monitor everything through Redis
5. **Scalable**: Add more agents without changing anything

The beauty is that each agent only needs to know:
- The project ID
- Its own session name
- How to call MCP tools

Everything else is handled by the infrastructure!