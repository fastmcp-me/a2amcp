# A2AMCP API Reference

## Table of Contents

1. [Overview](#overview)
2. [Core Concepts](#core-concepts)
3. [API Methods](#api-methods)
   - [Agent Management](#agent-management)
   - [Todo List Management](#todo-list-management)
   - [Communication](#communication)
   - [File Coordination](#file-coordination)
   - [Shared Definitions](#shared-definitions)
4. [Complete Examples](#complete-examples)
5. [Error Handling](#error-handling)
6. [Best Practices](#best-practices)

## Overview

A2AMCP provides MCP (Model Context Protocol) tools that AI agents use to communicate and coordinate. All methods follow a consistent pattern:

```python
tool_name(project_id: str, ...other_parameters) -> str
```

All responses are JSON-encoded strings containing status information and requested data.

## Core Concepts

### Project ID
Every API call requires a `project_id` to ensure isolation between different projects using the same A2AMCP server.

### Session Name
Each agent has a unique session name, typically formatted as `task-{task_id}` (e.g., `task-001`, `task-auth-123`).

### Response Format
All methods return JSON-encoded strings with at least a `status` field:
```json
{
  "status": "success|error|timeout|...",
  "message": "Human-readable message",
  "data": { ... }
}
```

## API Methods

### Agent Management

#### `register_agent`

Registers an agent with the A2AMCP server. This must be the first call made by any agent.

**Parameters:**
- `project_id` (str): Unique project identifier
- `session_name` (str): Unique session name for this agent
- `task_id` (str): Task identifier
- `branch` (str): Git branch name
- `description` (str): Brief description of the task

**Returns:**
```json
{
  "status": "registered",
  "project_id": "ecommerce-v2",
  "session_name": "task-001",
  "other_active_agents": ["task-002", "task-003"],
  "message": "Successfully registered. 2 other agents are active in this project."
}
```

**Example:**
```python
register_agent(
    "ecommerce-v2",
    "task-auth-001",
    "001",
    "feature/authentication",
    "Implement user authentication with JWT tokens"
)
```

---

#### `heartbeat`

Sends a keep-alive signal. Must be called every 30-60 seconds or the agent will be considered dead and cleaned up.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name

**Returns:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Example:**
```python
# In your agent's main loop
import time
while working:
    heartbeat("ecommerce-v2", "task-auth-001")
    time.sleep(30)
```

---

#### `list_active_agents`

Gets all currently active agents in the project.

**Parameters:**
- `project_id` (str): Project identifier

**Returns:**
```json
{
  "task-auth-001": {
    "task_id": "001",
    "branch": "feature/authentication",
    "description": "Implement user authentication with JWT tokens",
    "status": "active",
    "started_at": "2024-01-15T10:00:00Z"
  },
  "task-profile-002": {
    "task_id": "002",
    "branch": "feature/user-profiles",
    "description": "Create user profile management",
    "status": "active",
    "started_at": "2024-01-15T10:05:00Z"
  }
}
```

**Example:**
```python
agents = list_active_agents("ecommerce-v2")
print(f"Active agents: {len(agents)}")
for session, info in agents.items():
    print(f"  {session}: {info['description']}")
```

---

#### `unregister_agent`

Unregisters an agent when its task is complete. Shows todo completion summary.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name

**Returns:**
```json
{
  "status": "unregistered",
  "todo_summary": {
    "total": 5,
    "completed": 4,
    "pending": 1,
    "in_progress": 0
  },
  "message": "Successfully unregistered. Completed 4/5 todos."
}
```

**Example:**
```python
# When agent completes its task
result = unregister_agent("ecommerce-v2", "task-auth-001")
print(f"Task complete: {result['message']}")
```

### Todo List Management

#### `add_todo`

Adds a todo item to the agent's task breakdown.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `todo_item` (str): Description of the todo
- `priority` (int): Priority level (1=high, 2=medium, 3=low)

**Returns:**
```json
{
  "status": "added",
  "todo_id": "todo-1705320600.123",
  "message": "Added todo: Research JWT libraries"
}
```

**Example:**
```python
# Break down your task into todos
add_todo("ecommerce-v2", "task-auth-001", "Research JWT best practices", 1)
add_todo("ecommerce-v2", "task-auth-001", "Design User database schema", 1)
add_todo("ecommerce-v2", "task-auth-001", "Implement password hashing", 1)
add_todo("ecommerce-v2", "task-auth-001", "Create login endpoint", 2)
add_todo("ecommerce-v2", "task-auth-001", "Write authentication tests", 2)
```

---

#### `update_todo`

Updates the status of a todo item.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `todo_id` (str): ID of the todo to update
- `status` (str): New status (`pending`, `in_progress`, `completed`, `blocked`)

**Returns:**
```json
{
  "status": "updated",
  "todo_id": "todo-1705320600.123",
  "new_status": "completed"
}
```

**Example:**
```python
# Start working on a todo
update_todo("ecommerce-v2", "task-auth-001", "todo-1705320600.123", "in_progress")

# Complete it
update_todo("ecommerce-v2", "task-auth-001", "todo-1705320600.123", "completed")

# Mark as blocked if waiting for another agent
update_todo("ecommerce-v2", "task-auth-001", "todo-1705320600.456", "blocked")
```

---

#### `get_my_todos`

Gets all todos for the current agent.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name

**Returns:**
```json
{
  "session_name": "task-auth-001",
  "total": 5,
  "todos": [
    {
      "id": "todo-1705320600.123",
      "text": "Research JWT best practices",
      "status": "completed",
      "priority": 1,
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "todo-1705320600.456",
      "text": "Design User database schema",
      "status": "in_progress",
      "priority": 1,
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": null
    }
  ]
}
```

---

#### `get_all_todos`

Gets todos for all agents in the project. Useful for coordination.

**Parameters:**
- `project_id` (str): Project identifier

**Returns:**
```json
{
  "task-auth-001": {
    "task_id": "001",
    "description": "Implement user authentication",
    "total_todos": 5,
    "completed": 2,
    "todos": [...]
  },
  "task-profile-002": {
    "task_id": "002",
    "description": "Create user profiles",
    "total_todos": 4,
    "completed": 1,
    "todos": [...]
  }
}
```

**Example:**
```python
# Check what everyone is working on
all_todos = get_all_todos("ecommerce-v2")
for agent, info in all_todos.items():
    print(f"{agent}: {info['completed']}/{info['total_todos']} completed")
    
    # Find specific todos
    for todo in info['todos']:
        if 'User model' in todo['text']:
            print(f"  Found relevant todo: {todo['text']} - {todo['status']}")
```

### Communication

#### `query_agent`

Sends a query to another agent and optionally waits for a response.

**Parameters:**
- `project_id` (str): Project identifier
- `from_session` (str): Your session name
- `to_session` (str): Target agent's session name
- `query_type` (str): Type of query (e.g., "interface", "help", "status")
- `query` (str): The actual question
- `wait_for_response` (bool): Whether to wait for response (default: True)
- `timeout` (int): Seconds to wait for response (default: 30)

**Returns (if waiting):**
```json
{
  "status": "received",
  "response": "The User interface has id, email, password, and role fields"
}
```

**Returns (if not waiting):**
```json
{
  "status": "sent",
  "message_id": "task-auth-001-1705320600.789"
}
```

**Example:**
```python
# Ask about an interface
response = query_agent(
    "ecommerce-v2",
    "task-profile-002",
    "task-auth-001",
    "interface",
    "What fields does the User interface have? I need to extend it for profiles."
)

# Ask for help
response = query_agent(
    "ecommerce-v2",
    "task-frontend-003",
    "task-auth-001",
    "help",
    "How should I handle authentication tokens in the frontend?",
    timeout=60  # Give more time for complex questions
)
```

---

#### `check_messages`

Checks for any messages sent to this agent. Clears the queue after reading.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name

**Returns:**
```json
[
  {
    "id": "msg-123",
    "from": "task-profile-002",
    "type": "query",
    "query_type": "interface",
    "content": "What fields does the User interface have?",
    "timestamp": "2024-01-15T10:30:00Z",
    "requires_response": true
  },
  {
    "from": "task-frontend-003",
    "type": "broadcast",
    "message_type": "info",
    "content": "Starting work on the login UI",
    "timestamp": "2024-01-15T10:35:00Z"
  }
]
```

**Example:**
```python
# Check messages periodically
messages = check_messages("ecommerce-v2", "task-auth-001")
for msg in messages:
    if msg['type'] == 'query' and msg.get('requires_response'):
        # Respond to the query
        if 'User interface' in msg['content']:
            respond_to_query(
                "ecommerce-v2",
                "task-auth-001",
                msg['from'],
                msg['id'],
                "User has: id (string), email (string), password (hashed), role (string), createdAt (Date)"
            )
```

---

#### `respond_to_query`

Responds to a query from another agent.

**Parameters:**
- `project_id` (str): Project identifier
- `from_session` (str): Your session name
- `to_session` (str): Session that sent the query
- `message_id` (str): ID of the original query
- `response` (str): Your response

**Returns:**
```json
{
  "status": "response_sent",
  "to": "task-profile-002"
}
```

---

#### `broadcast_message`

Sends a message to all other agents in the project.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Your session name
- `message_type` (str): Type of broadcast ("info", "warning", "help_needed")
- `content` (str): The message content

**Returns:**
```json
{
  "status": "broadcast_sent",
  "recipients": 3
}
```

**Example:**
```python
# Announce important changes
broadcast_message(
    "ecommerce-v2",
    "task-auth-001",
    "warning",
    "I'm refactoring the User model to add roles. This may affect your interfaces!"
)

# Ask for help from anyone
broadcast_message(
    "ecommerce-v2",
    "task-frontend-003",
    "help_needed",
    "Does anyone know the best practice for storing JWT tokens in React?"
)
```

### File Coordination

#### `announce_file_change`

Announces intention to modify a file. Prevents conflicts by locking the file.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `file_path` (str): Path to the file
- `change_type` (str): Type of change ("create", "modify", "delete", "refactor")
- `description` (str): What you're planning to do

**Returns (success):**
```json
{
  "status": "locked",
  "file_path": "src/models/user.ts",
  "message": "File locked successfully. Remember to release when done."
}
```

**Returns (conflict):**
```json
{
  "status": "conflict",
  "error": "File is locked by task-profile-002",
  "lock_info": {
    "session": "task-profile-002",
    "locked_at": "2024-01-15T10:30:00Z",
    "change_type": "modify",
    "description": "Adding profile fields to User model"
  },
  "suggestion": "Query that agent about their progress or wait"
}
```

**Example:**
```python
# Before modifying a file
result = announce_file_change(
    "ecommerce-v2",
    "task-auth-001",
    "src/models/user.ts",
    "create",
    "Creating User model with authentication fields"
)

if result['status'] == 'conflict':
    # File is locked by another agent
    other_agent = result['lock_info']['session']
    # Query them about timeline
    response = query_agent(
        "ecommerce-v2",
        "task-auth-001",
        other_agent,
        "status",
        f"When will you be done with {file_path}? I need to add auth fields."
    )
else:
    # File is locked, safe to modify
    # ... do your work ...
    # Then release the lock
    release_file_lock("ecommerce-v2", "task-auth-001", "src/models/user.ts")
```

---

#### `release_file_lock`

Releases a file lock after completing changes.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `file_path` (str): Path to the file

**Returns:**
```json
{
  "status": "released",
  "file_path": "src/models/user.ts"
}
```

---

#### `get_recent_changes`

Gets recent file changes across all agents in the project.

**Parameters:**
- `project_id` (str): Project identifier
- `limit` (int): Maximum number of changes to return (default: 20)

**Returns:**
```json
[
  {
    "session": "task-auth-001",
    "file_path": "src/models/user.ts",
    "change_type": "create",
    "description": "Created User model with auth fields",
    "timestamp": "2024-01-15T10:45:00Z"
  },
  {
    "session": "task-api-003",
    "file_path": "src/routes/auth.ts",
    "change_type": "create",
    "description": "Added login and register endpoints",
    "timestamp": "2024-01-15T10:40:00Z"
  }
]
```

**Example:**
```python
# Check what files were recently modified
changes = get_recent_changes("ecommerce-v2", limit=10)
for change in changes:
    print(f"{change['session']} {change['change_type']}d {change['file_path']}")
```

### Shared Definitions

#### `register_interface`

Registers a shared interface or type definition that other agents can use.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `interface_name` (str): Name of the interface/type
- `definition` (str): The complete definition
- `file_path` (str, optional): Where this interface is defined

**Returns:**
```json
{
  "status": "registered",
  "interface_name": "User",
  "message": "Interface registered and available to all agents"
}
```

**Example:**
```python
# After creating a TypeScript interface
register_interface(
    "ecommerce-v2",
    "task-auth-001",
    "User",
    """interface User {
  id: string;
  email: string;
  password: string;
  role: 'admin' | 'user' | 'guest';
  createdAt: Date;
  updatedAt: Date;
}""",
    "src/types/user.ts"
)

# Register a type
register_interface(
    "ecommerce-v2",
    "task-auth-001",
    "UserRole",
    "type UserRole = 'admin' | 'user' | 'guest';",
    "src/types/user.ts"
)

# Register an API response type
register_interface(
    "ecommerce-v2",
    "task-api-003",
    "LoginResponse",
    """interface LoginResponse {
  user: User;
  token: string;
  expiresIn: number;
}""",
    "src/types/api.ts"
)
```

---

#### `query_interface`

Gets a registered interface definition.

**Parameters:**
- `project_id` (str): Project identifier
- `interface_name` (str): Name of the interface to query

**Returns (found):**
```json
{
  "definition": "interface User { id: string; email: string; ... }",
  "registered_by": "task-auth-001",
  "file_path": "src/types/user.ts",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Returns (not found):**
```json
{
  "status": "not_found",
  "error": "Interface User not found",
  "similar": ["UserProfile", "UserRole"]
}
```

**Example:**
```python
# Get an interface definition
user_interface = query_interface("ecommerce-v2", "User")
if user_interface.get('status') != 'not_found':
    print(f"User interface: {user_interface['definition']}")
    print(f"Defined in: {user_interface['file_path']}")
else:
    # Interface doesn't exist yet
    similar = user_interface.get('similar', [])
    if similar:
        print(f"Did you mean: {', '.join(similar)}?")
```

---

#### `list_interfaces`

Lists all registered interfaces in the project.

**Parameters:**
- `project_id` (str): Project identifier

**Returns:**
```json
{
  "User": {
    "definition": "interface User { ... }",
    "registered_by": "task-auth-001",
    "file_path": "src/types/user.ts",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "UserProfile": {
    "definition": "interface UserProfile extends User { ... }",
    "registered_by": "task-profile-002",
    "file_path": "src/types/profile.ts",
    "timestamp": "2024-01-15T10:45:00Z"
  }
}
```

## Complete Examples

### Example 1: Authentication Agent Workflow

```python
# Start of authentication agent
project_id = "ecommerce-v2"
session_name = "task-auth-001"

# 1. Register
register_agent(project_id, session_name, "001", "feature/auth", "Build authentication system")

# 2. Create todo list
todos = [
    ("Research JWT best practices", 1),
    ("Design User schema", 1),
    ("Implement password hashing", 1),
    ("Create login endpoint", 2),
    ("Create register endpoint", 2),
    ("Add authentication middleware", 2),
    ("Write tests", 3)
]

todo_ids = []
for text, priority in todos:
    result = add_todo(project_id, session_name, text, priority)
    todo_ids.append(result['todo_id'])

# 3. Start working
update_todo(project_id, session_name, todo_ids[0], "in_progress")

# 4. Check who else is active
agents = list_active_agents(project_id)
print(f"Working with {len(agents) - 1} other agents")

# 5. Create User model
result = announce_file_change(
    project_id, 
    session_name,
    "src/models/user.ts",
    "create",
    "Creating User model with authentication fields"
)

if result['status'] == 'locked':
    # Create the file...
    # Then register the interface
    register_interface(
        project_id,
        session_name,
        "User",
        """interface User {
  id: string;
  email: string;
  password: string;  // bcrypt hashed
  role: 'admin' | 'user' | 'guest';
  emailVerified: boolean;
  createdAt: Date;
  updatedAt: Date;
}""",
        "src/models/user.ts"
    )
    
    # Release the lock
    release_file_lock(project_id, session_name, "src/models/user.ts")
    
    # Update todo
    update_todo(project_id, session_name, todo_ids[1], "completed")
    
    # Broadcast completion
    broadcast_message(
        project_id,
        session_name,
        "info",
        "User model is ready! Interface 'User' is now available."
    )

# 6. Periodically check messages and send heartbeat
import time
while working:
    # Send heartbeat
    heartbeat(project_id, session_name)
    
    # Check messages
    messages = check_messages(project_id, session_name)
    for msg in messages:
        if msg['type'] == 'query':
            if 'User' in msg['content']:
                respond_to_query(
                    project_id,
                    session_name,
                    msg['from'],
                    msg['id'],
                    "User interface has: id, email, password (hashed), role, emailVerified, timestamps"
                )
    
    time.sleep(30)

# 7. Complete task
unregister_agent(project_id, session_name)
```

### Example 2: Frontend Agent Needing Backend Info

```python
# Frontend agent starting work
project_id = "ecommerce-v2"
session_name = "task-frontend-003"

# 1. Register
register_agent(project_id, session_name, "003", "feature/login-ui", "Build login interface")

# 2. Check what backend agents are doing
all_todos = get_all_todos(project_id)
auth_agent = None

for agent, info in all_todos.items():
    if 'auth' in info['description'].lower():
        auth_agent = agent
        # Check if login endpoint is ready
        for todo in info['todos']:
            if 'login endpoint' in todo['text']:
                if todo['status'] == 'completed':
                    print("Great! Login endpoint is ready")
                else:
                    print(f"Login endpoint status: {todo['status']}")

# 3. Query for API details
if auth_agent:
    response = query_agent(
        project_id,
        session_name,
        auth_agent,
        "api",
        "What's the login endpoint URL and what data does it expect?"
    )
    print(f"Login API details: {response}")

# 4. Get User interface
user_interface = query_interface(project_id, "User")
if user_interface.get('status') != 'not_found':
    print(f"User interface available: {user_interface['definition']}")
else:
    # Wait or ask for it
    broadcast_message(
        project_id,
        session_name,
        "help_needed",
        "I need the User interface to build the login form. Has anyone created it?"
    )

# 5. Work on login component
result = announce_file_change(
    project_id,
    session_name,
    "src/components/LoginForm.tsx",
    "create",
    "Creating login form component"
)

if result['status'] == 'locked':
    # Build the component using the User interface
    # ...
    release_file_lock(project_id, session_name, "src/components/LoginForm.tsx")
```

### Example 3: Coordinating Multiple Agents

```python
# API agent needs to coordinate with both auth and database agents
project_id = "ecommerce-v2"
session_name = "task-api-004"

# 1. Register
register_agent(project_id, session_name, "004", "feature/user-api", "Build user management API")

# 2. Check all interfaces
interfaces = list_interfaces(project_id)
print(f"Available interfaces: {list(interfaces.keys())}")

# 3. See what everyone is working on
all_todos = get_all_todos(project_id)

# Find agents working on related features
auth_agent = None
db_agent = None

for agent, info in all_todos.items():
    if 'auth' in info['description'].lower():
        auth_agent = agent
    elif 'database' in info['description'].lower():
        db_agent = agent

# 4. Query multiple agents
if auth_agent:
    auth_response = query_agent(
        project_id,
        session_name,
        auth_agent,
        "interface",
        "What auth middleware should I use for protecting user endpoints?"
    )

if db_agent:
    db_response = query_agent(
        project_id,
        session_name,
        db_agent,
        "help",
        "What's the database connection pattern we're using?"
    )

# 5. Register API contracts for others to use
register_interface(
    project_id,
    session_name,
    "UserAPI",
    """interface UserAPI {
  GET /api/users - List all users (admin only)
  GET /api/users/:id - Get user by ID
  PUT /api/users/:id - Update user
  DELETE /api/users/:id - Delete user (admin only)
  
  All endpoints require Authorization: Bearer <token>
}""",
    "src/routes/users.ts"
)

# 6. Check for conflicts before working on shared files
shared_files = ["src/app.ts", "src/routes/index.ts"]
for file_path in shared_files:
    result = announce_file_change(
        project_id,
        session_name,
        file_path,
        "modify",
        "Adding user routes to main app"
    )
    
    if result['status'] == 'conflict':
        # Someone else is working on it
        lock_info = result['lock_info']
        print(f"{file_path} is locked by {lock_info['session']}")
        print(f"They are: {lock_info['description']}")
        
        # Query them about timeline
        response = query_agent(
            project_id,
            session_name,
            lock_info['session'],
            "status",
            f"When will you be done with {file_path}? I need to add user routes."
        )
```

## Error Handling

### Common Error Responses

```python
# Agent not found
{
  "error": "Agent task-999 not found in project ecommerce-v2"
}

# File conflict
{
  "status": "conflict",
  "error": "File is locked by task-auth-001",
  "lock_info": { ... }
}

# Interface not found
{
  "status": "not_found",
  "error": "Interface UserProfile not found",
  "similar": ["User", "Profile"]
}

# Query timeout
{
  "status": "timeout",
  "error": "No response received within 30 seconds"
}
```

### Error Handling Pattern

```python
def safe_query_interface(project_id, interface_name):
    """Safely query an interface with fallback"""
    result = query_interface(project_id, interface_name)
    
    if isinstance(result, dict) and result.get('status') == 'not_found':
        # Interface doesn't exist
        similar = result.get('similar', [])
        if similar:
            print(f"Interface {interface_name} not found. Similar: {similar}")
            # Try the first similar one
            if similar:
                return query_interface(project_id, similar[0])
        return None
    
    return result

def safe_file_change(project_id, session_name, file_path, change_type, description, max_retries=3):
    """Try to lock a file with retries"""
    for attempt in range(max_retries):
        result = announce_file_change(project_id, session_name, file_path, change_type, description)
        
        if result['status'] == 'locked':
            return True
        
        if result['status'] == 'conflict':
            print(f"Attempt {attempt + 1}: File locked by {result['lock_info']['session']}")
            if attempt < max_retries - 1:
                time.sleep(10)  # Wait 10 seconds before retry
            else:
                return False
    
    return False
```

## Best Practices

### 1. Always Register First
```python
# ALWAYS do this first
register_agent(project_id, session_name, task_id, branch, description)
```

### 2. Maintain Heartbeat
```python
# In your main loop
while working:
    heartbeat(project_id, session_name)
    # Do work...
    time.sleep(30)
```

### 3. Create Detailed Todos
```python
# Good: Specific and actionable
add_todo(project_id, session_name, "Implement bcrypt password hashing with salt rounds=10", 1)

# Bad: Too vague
add_todo(project_id, session_name, "Do authentication", 1)
```

### 4. Check Messages Regularly
```python
# Check every 30-60 seconds
messages = check_messages(project_id, session_name)
for msg in messages:
    # Process each message appropriately
    handle_message(msg)
```

### 5. Always Release Locks
```python
try:
    result = announce_file_change(project_id, session_name, file_path, "modify", "Updating")
    if result['status'] == 'locked':
        # Do your work
        modify_file(file_path)
finally:
    # ALWAYS release, even if error occurs
    release_file_lock(project_id, session_name, file_path)
```

### 6. Query Before Assuming
```python
# Don't assume an interface exists
user_interface = query_interface(project_id, "User")
if user_interface.get('status') == 'not_found':
    # Handle missing interface
    query_agent(project_id, session_name, "task-auth-001", "interface", "Is the User interface ready?")
```

### 7. Broadcast Important Changes
```python
# Let everyone know about breaking changes
broadcast_message(
    project_id,
    session_name,
    "warning",
    "Changing User.id from number to string UUID. Update your code!"
)
```

### 8. Clean Exit
```python
# Always unregister when done
result = unregister_agent(project_id, session_name)
print(f"Completed {result['todo_summary']['completed']} todos")
```

---

*This API reference is part of the A2AMCP project. For more information, visit [github.com/webdevtodayjason/A2AMCP](https://github.com/webdevtodayjason/A2AMCP)*