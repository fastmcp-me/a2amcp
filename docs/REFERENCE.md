# A2AMCP API Reference

This document provides a complete reference for all A2AMCP MCP tools. For SDK-specific documentation, see the respective SDK directories.

## Table of Contents

1. [Overview](#overview)
2. [Connection](#connection)
3. [Agent Management](#agent-management)
4. [Todo Management](#todo-management)
5. [Communication](#communication)
6. [File Coordination](#file-coordination)
7. [Shared Definitions](#shared-definitions)
8. [Response Formats](#response-formats)
9. [Error Handling](#error-handling)
10. [Best Practices](#best-practices)

## Overview

A2AMCP provides Model Context Protocol (MCP) tools for agent communication. All tools follow this pattern:

```
tool_name(project_id: str, ...parameters) -> JSON string
```

### Common Parameters

- `project_id` (str): Required for all tools. Isolates different projects.
- `session_name` (str): Agent's unique identifier, typically `task-{id}`.

### Authentication

Currently, A2AMCP does not require authentication. Future versions will support API keys and OAuth.

## Connection

### Server URL

Default: `localhost:5000`

Docker: The MCP server runs inside the container. Agents connect via:
```json
{
  "mcpServers": {
    "a2amcp": {
      "command": "docker",
      "args": ["exec", "-i", "a2amcp-server", "python", "/app/mcp_server_redis.py"]
    }
  }
}
```

## Agent Management

### `register_agent`

Registers an agent with the server. **Must be called first by every agent.**

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Unique session name
- `task_id` (str): Task identifier  
- `branch` (str): Git branch name
- `description` (str): Task description

**Returns:**
```json
{
  "status": "registered",
  "project_id": "my-project",
  "session_name": "task-001",
  "other_active_agents": ["task-002", "task-003"],
  "message": "Successfully registered. 2 other agents are active in this project."
}
```

**Example:**
```python
register_agent("ecommerce", "task-001", "001", "feature/auth", "Implement user authentication")
```

---

### `heartbeat`

Sends a keep-alive signal. Must be called every 30-60 seconds.

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

---

### `list_active_agents`

Lists all active agents in the project.

**Parameters:**
- `project_id` (str): Project identifier

**Returns:**
```json
{
  "task-001": {
    "task_id": "001",
    "branch": "feature/auth",
    "description": "Implement user authentication",
    "status": "active",
    "started_at": "2024-01-15T10:00:00Z"
  },
  "task-002": {
    "task_id": "002",
    "branch": "feature/profile",
    "description": "Create user profiles",
    "status": "active",
    "started_at": "2024-01-15T10:05:00Z"
  }
}
```

---

### `mark_task_completed`

Marks a task as completed and signals the orchestrator.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `task_id` (str): Task identifier that was completed

**Returns:**
```json
{
  "status": "success",
  "message": "Task TASK-123 marked as completed"
}
```

**Effects:**
- Updates agent status to "completed" in Redis
- Stores completion record with timestamp
- Writes "COMPLETED" to `/tmp/splitmind-status/{session_name}.status`
- Allows orchestrator to detect and handle completion

---

### `unregister_agent`

Unregisters an agent when task is complete.

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

## Todo Management

### `add_todo`

Adds a todo item to the agent's task list.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `todo_item` (str): Description of the todo
- `priority` (int): Priority (1=high, 2=medium, 3=low)

**Returns:**
```json
{
  "status": "added",
  "todo_id": "todo-1705320600.123456",
  "message": "Added todo: Research JWT libraries"
}
```

---

### `update_todo`

Updates todo status.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `todo_id` (str): Todo identifier
- `status` (str): New status (`pending`, `in_progress`, `completed`, `blocked`)

**Returns:**
```json
{
  "status": "updated",
  "todo_id": "todo-1705320600.123456",
  "new_status": "completed"
}
```

---

### `get_my_todos`

Gets agent's own todos.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name

**Returns:**
```json
{
  "session_name": "task-001",
  "total": 5,
  "todos": [
    {
      "id": "todo-1705320600.123",
      "text": "Research JWT best practices",
      "status": "completed",
      "priority": 1,
      "created_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

---

### `get_all_todos`

Gets todos for all agents in the project.

**Parameters:**
- `project_id` (str): Project identifier

**Returns:**
```json
{
  "task-001": {
    "task_id": "001",
    "description": "Implement authentication",
    "total_todos": 5,
    "completed": 3,
    "todos": [...]
  },
  "task-002": {
    "task_id": "002",
    "description": "Create user profiles",
    "total_todos": 4,
    "completed": 1,
    "todos": [...]
  }
}
```

## Communication

### `query_agent`

Sends a query to another agent.

**Parameters:**
- `project_id` (str): Project identifier
- `from_session` (str): Sender's session name
- `to_session` (str): Target agent's session name
- `query_type` (str): Type of query (`interface`, `api`, `help`, `status`)
- `query` (str): The question
- `wait_for_response` (bool): Whether to wait (default: true)
- `timeout` (int): Seconds to wait (default: 30)

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
  "message_id": "task-001-1705320600.789"
}
```

---

### `check_messages`

Checks for incoming messages. Clears queue after reading.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name

**Returns:**
```json
[
  {
    "id": "msg-123",
    "from": "task-002",
    "type": "query",
    "query_type": "interface",
    "content": "What fields does the User interface have?",
    "timestamp": "2024-01-15T10:30:00Z",
    "requires_response": true
  }
]
```

---

### `respond_to_query`

Responds to a query from another agent.

**Parameters:**
- `project_id` (str): Project identifier
- `from_session` (str): Responder's session name
- `to_session` (str): Original sender's session name
- `message_id` (str): Original message ID
- `response` (str): Response content

**Returns:**
```json
{
  "status": "response_sent",
  "to": "task-002"
}
```

---

### `broadcast_message`

Sends a message to all other agents.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Sender's session name
- `message_type` (str): Type (`info`, `warning`, `help_needed`)
- `content` (str): Message content

**Returns:**
```json
{
  "status": "broadcast_sent",
  "recipients": 3
}
```

## File Coordination

### `announce_file_change`

Announces intention to modify a file. Locks the file.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `file_path` (str): Path to file
- `change_type` (str): Type (`create`, `modify`, `delete`, `refactor`)
- `description` (str): Description of changes

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
  "error": "File is locked by task-002",
  "lock_info": {
    "session": "task-002",
    "locked_at": "2024-01-15T10:30:00Z",
    "change_type": "modify",
    "description": "Adding profile fields"
  },
  "suggestion": "Query that agent about their progress or wait"
}
```

---

### `release_file_lock`

Releases a file lock.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `file_path` (str): Path to file

**Returns:**
```json
{
  "status": "released",
  "file_path": "src/models/user.ts"
}
```

---

### `get_recent_changes`

Gets recent file changes across all agents.

**Parameters:**
- `project_id` (str): Project identifier
- `limit` (int): Maximum changes to return (default: 20)

**Returns:**
```json
[
  {
    "session": "task-001",
    "file_path": "src/models/user.ts",
    "change_type": "create",
    "description": "Created User model with auth fields",
    "timestamp": "2024-01-15T10:45:00Z"
  }
]
```

## Shared Definitions

### `register_interface`

Registers a shared interface/type definition.

**Parameters:**
- `project_id` (str): Project identifier
- `session_name` (str): Agent's session name
- `interface_name` (str): Name of interface
- `definition` (str): Complete definition
- `file_path` (str, optional): Where it's defined

**Returns:**
```json
{
  "status": "registered",
  "interface_name": "User",
  "message": "Interface registered and available to all agents"
}
```

---

### `query_interface`

Gets an interface definition.

**Parameters:**
- `project_id` (str): Project identifier
- `interface_name` (str): Name to query

**Returns (found):**
```json
{
  "definition": "interface User { id: string; email: string; }",
  "registered_by": "task-001",
  "file_path": "src/types/user.ts",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

**Returns (not found):**
```json
{
  "status": "not_found",
  "error": "Interface User not found",
  "similar": ["UserProfile", "UserAuth"]
}
```

---

### `list_interfaces`

Lists all registered interfaces.

**Parameters:**
- `project_id` (str): Project identifier

**Returns:**
```json
{
  "User": {
    "definition": "interface User { ... }",
    "registered_by": "task-001",
    "file_path": "src/types/user.ts",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

## Response Formats

### Success Response
```json
{
  "status": "success|registered|locked|...",
  "data": { ... },
  "message": "Human-readable message"
}
```

### Error Response
```json
{
  "status": "error|conflict|not_found|timeout",
  "error": "Error description",
  "details": { ... }
}
```

### List Response
Arrays are returned directly:
```json
[
  { "item": 1 },
  { "item": 2 }
]
```

## Error Handling

### Common Errors

| Error | Description | Resolution |
|-------|-------------|------------|
| `agent_not_found` | Target agent doesn't exist | Check `list_active_agents` |
| `file_locked` | File is being modified | Query lock owner or wait |
| `interface_not_found` | Interface not registered | Check similar names |
| `timeout` | No response in time | Retry or broadcast |
| `not_registered` | Agent not registered | Call `register_agent` first |

### Retry Strategy

```python
# Recommended retry logic
max_retries = 3
retry_delay = 5  # seconds

for attempt in range(max_retries):
    try:
        result = announce_file_change(...)
        if result['status'] == 'locked':
            break
    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
        else:
            raise
```

## Best Practices

### 1. Registration
- Always register immediately on startup
- Handle registration failures gracefully
- Include descriptive task information

### 2. Heartbeats
- Send every 30-45 seconds
- Don't exceed 60 seconds
- Handle heartbeat failures silently

### 3. Message Checking
- Check every 20-30 seconds
- Process all messages in queue
- Respond to queries promptly

### 4. File Coordination
- Always announce before modifying
- Release locks immediately after changes
- Handle conflicts gracefully

### 5. Interface Sharing
- Register interfaces as soon as created
- Use consistent naming conventions
- Include complete definitions

### 6. Error Handling
- Implement retry logic
- Log errors for debugging
- Fail gracefully

### 7. Task Completion
- Call `mark_task_completed` when work is done
- This signals the orchestrator properly
- Then call `unregister_agent` for cleanup

### 8. Cleanup
- Always unregister on exit
- Release all held locks
- Complete or update todos

## Rate Limits

Current limits (subject to change):
- Heartbeat: Min 10s between calls
- Message checks: Max 10/minute
- Queries: Max 100/minute
- File operations: No limit

## Versioning

Current version: 1.0.0

The API follows semantic versioning:
- Major: Breaking changes
- Minor: New features, backward compatible
- Patch: Bug fixes

## Migration Guide

Future versions will include migration guides for breaking changes.

---

For language-specific implementations, see:
- [Python SDK](../sdk/python/README.md)
- [JavaScript SDK](../sdk/javascript/README.md) (coming soon)
- [Go SDK](../sdk/go/README.md) (planned)