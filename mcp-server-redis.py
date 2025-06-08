#!/usr/bin/env python3
"""
SplitMind Agent Communication MCP Server with Redis Backend

Multi-project MCP server that enables communication between AI agents
with persistent state storage in Redis.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis.asyncio as redis
from contextlib import asynccontextmanager

from mcp.server import Server
from mcp.server.stdio import stdio_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('splitmind-mcp')


class AgentCommunicationServer:
    """MCP Server with Redis backend for multi-project agent communication"""
    
    def __init__(self, redis_url: str = None):
        self.server = Server("splitmind-agent-comm")
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client: Optional[redis.Redis] = None
        self.heartbeat_timeout = 120  # seconds
        self._setup_tools()
    
    async def initialize(self):
        """Initialize Redis connection"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        logger.info(f"Connected to Redis at {self.redis_url}")
        
        # Start heartbeat monitor
        asyncio.create_task(self._heartbeat_monitor())
    
    async def cleanup(self):
        """Cleanup Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    def _get_key(self, project_id: str, key_type: str, *args) -> str:
        """Generate Redis key with project namespace"""
        parts = [f"project:{project_id}", key_type] + list(args)
        return ":".join(parts)
    
    async def _update_heartbeat(self, project_id: str, session_name: str):
        """Update agent heartbeat"""
        key = self._get_key(project_id, "heartbeat", session_name)
        await self.redis_client.setex(key, self.heartbeat_timeout, datetime.now().isoformat())
    
    async def _heartbeat_monitor(self):
        """Monitor agent heartbeats and clean up dead agents"""
        while True:
            try:
                # Check all projects
                project_keys = await self.redis_client.keys("project:*:agents")
                
                for project_key in project_keys:
                    project_id = project_key.split(":")[1]
                    agents = await self.redis_client.hgetall(project_key)
                    
                    for session_name, agent_data in agents.items():
                        heartbeat_key = self._get_key(project_id, "heartbeat", session_name)
                        heartbeat = await self.redis_client.get(heartbeat_key)
                        
                        if not heartbeat:
                            # No heartbeat found, remove agent
                            await self._cleanup_dead_agent(project_id, session_name)
                            logger.warning(f"Cleaned up dead agent {session_name} in project {project_id}")
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _cleanup_dead_agent(self, project_id: str, session_name: str):
        """Clean up resources for a dead agent"""
        # Release all file locks
        locks_key = self._get_key(project_id, "locks")
        all_locks = await self.redis_client.hgetall(locks_key)
        
        for file_path, lock_data in all_locks.items():
            lock_info = json.loads(lock_data)
            if lock_info.get("session") == session_name:
                await self.redis_client.hdel(locks_key, file_path)
        
        # Remove from active agents
        agents_key = self._get_key(project_id, "agents")
        await self.redis_client.hdel(agents_key, session_name)
        
        # Clean up message queue
        messages_key = self._get_key(project_id, "messages", session_name)
        await self.redis_client.delete(messages_key)
        
        # Clean up todos
        todos_key = self._get_key(project_id, "todos", session_name)
        await self.redis_client.delete(todos_key)
    
    def _setup_tools(self):
        """Register all MCP tools"""
        
        @self.server.tool()
        async def register_agent(
            project_id: str,
            session_name: str,
            task_id: str,
            branch: str,
            description: str
        ) -> str:
            """
            Register an agent for a specific project.
            
            Args:
                project_id: Unique project identifier
                session_name: Unique tmux session name (e.g., "task-123")
                task_id: The task ID this agent is working on
                branch: Git branch name for this task
                description: Brief description of the task
            """
            # Store agent info
            agent_data = {
                "task_id": task_id,
                "branch": branch,
                "description": description,
                "status": "active",
                "started_at": datetime.now().isoformat(),
                "project_id": project_id
            }
            
            agents_key = self._get_key(project_id, "agents")
            await self.redis_client.hset(agents_key, session_name, json.dumps(agent_data))
            
            # Set initial heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            # Initialize empty todo list
            todos_key = self._get_key(project_id, "todos", session_name)
            await self.redis_client.delete(todos_key)  # Clear any old todos
            
            # Notify other agents in the project
            await self._broadcast_event(project_id, {
                "type": "agent_joined",
                "session_name": session_name,
                "description": description
            }, exclude=session_name)
            
            # Get other active agents in this project
            all_agents = await self.redis_client.hgetall(agents_key)
            other_agents = [s for s in all_agents.keys() if s != session_name]
            
            logger.info(f"Agent {session_name} registered for project {project_id}")
            
            return json.dumps({
                "status": "registered",
                "project_id": project_id,
                "session_name": session_name,
                "other_active_agents": other_agents,
                "message": f"Successfully registered. {len(other_agents)} other agents are active in this project."
            })
        
        @self.server.tool()
        async def heartbeat(project_id: str, session_name: str) -> str:
            """
            Send a heartbeat to indicate the agent is still alive.
            Should be called periodically (every 30-60 seconds).
            """
            await self._update_heartbeat(project_id, session_name)
            return json.dumps({"status": "ok", "timestamp": datetime.now().isoformat()})
        
        @self.server.tool()
        async def list_active_agents(project_id: str) -> str:
            """Get all active agents in a specific project."""
            agents_key = self._get_key(project_id, "agents")
            agents_data = await self.redis_client.hgetall(agents_key)
            
            agents = {}
            for session_name, data in agents_data.items():
                agents[session_name] = json.loads(data)
            
            return json.dumps(agents, indent=2)
        
        @self.server.tool()
        async def add_todo(
            project_id: str,
            session_name: str,
            todo_item: str,
            priority: int = 1
        ) -> str:
            """
            Add a todo item to the agent's task list.
            
            Args:
                project_id: Project identifier
                session_name: Agent's session name
                todo_item: Description of the todo
                priority: Priority level (1=high, 2=medium, 3=low)
            """
            todo = {
                "id": f"todo-{datetime.now().timestamp()}",
                "text": todo_item,
                "status": "pending",
                "priority": priority,
                "created_at": datetime.now().isoformat(),
                "completed_at": None
            }
            
            todos_key = self._get_key(project_id, "todos", session_name)
            await self.redis_client.rpush(todos_key, json.dumps(todo))
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            return json.dumps({
                "status": "added",
                "todo_id": todo["id"],
                "message": f"Added todo: {todo_item}"
            })
        
        @self.server.tool()
        async def update_todo(
            project_id: str,
            session_name: str,
            todo_id: str,
            status: str
        ) -> str:
            """
            Update the status of a todo item.
            
            Args:
                project_id: Project identifier
                session_name: Agent's session name
                todo_id: ID of the todo to update
                status: New status (pending, in_progress, completed, blocked)
            """
            todos_key = self._get_key(project_id, "todos", session_name)
            todos = await self.redis_client.lrange(todos_key, 0, -1)
            
            updated = False
            new_todos = []
            
            for todo_str in todos:
                todo = json.loads(todo_str)
                if todo["id"] == todo_id:
                    todo["status"] = status
                    if status == "completed":
                        todo["completed_at"] = datetime.now().isoformat()
                    updated = True
                new_todos.append(json.dumps(todo))
            
            if updated:
                # Replace the entire list
                await self.redis_client.delete(todos_key)
                if new_todos:
                    await self.redis_client.rpush(todos_key, *new_todos)
                
                # Broadcast completion if completed
                if status == "completed":
                    await self._broadcast_event(project_id, {
                        "type": "todo_completed",
                        "session_name": session_name,
                        "todo_id": todo_id
                    })
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            return json.dumps({
                "status": "updated" if updated else "not_found",
                "todo_id": todo_id,
                "new_status": status
            })
        
        @self.server.tool()
        async def get_my_todos(project_id: str, session_name: str) -> str:
            """Get all todos for the current agent."""
            todos_key = self._get_key(project_id, "todos", session_name)
            todos_raw = await self.redis_client.lrange(todos_key, 0, -1)
            
            todos = [json.loads(todo) for todo in todos_raw]
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            return json.dumps({
                "session_name": session_name,
                "total": len(todos),
                "todos": todos
            }, indent=2)
        
        @self.server.tool()
        async def get_all_todos(project_id: str) -> str:
            """Get todos for all agents in the project."""
            agents_key = self._get_key(project_id, "agents")
            agents = await self.redis_client.hkeys(agents_key)
            
            all_todos = {}
            
            for session_name in agents:
                todos_key = self._get_key(project_id, "todos", session_name)
                todos_raw = await self.redis_client.lrange(todos_key, 0, -1)
                todos = [json.loads(todo) for todo in todos_raw]
                
                # Get agent info
                agent_data = await self.redis_client.hget(agents_key, session_name)
                agent_info = json.loads(agent_data) if agent_data else {}
                
                all_todos[session_name] = {
                    "task_id": agent_info.get("task_id"),
                    "description": agent_info.get("description"),
                    "total_todos": len(todos),
                    "completed": len([t for t in todos if t["status"] == "completed"]),
                    "todos": todos
                }
            
            return json.dumps(all_todos, indent=2)
        
        @self.server.tool()
        async def query_agent(
            project_id: str,
            from_session: str,
            to_session: str,
            query_type: str,
            query: str,
            wait_for_response: bool = True,
            timeout: int = 30
        ) -> str:
            """Send a query to another agent in the same project."""
            # Check if target agent exists
            agents_key = self._get_key(project_id, "agents")
            if not await self.redis_client.hexists(agents_key, to_session):
                return json.dumps({
                    "error": f"Agent {to_session} not found in project {project_id}"
                })
            
            message_id = f"{from_session}-{datetime.now().timestamp()}"
            message = {
                "id": message_id,
                "from": from_session,
                "type": "query",
                "query_type": query_type,
                "content": query,
                "timestamp": datetime.now().isoformat(),
                "requires_response": wait_for_response
            }
            
            # Add to target's message queue
            messages_key = self._get_key(project_id, "messages", to_session)
            await self.redis_client.rpush(messages_key, json.dumps(message))
            
            # Update heartbeat
            await self._update_heartbeat(project_id, from_session)
            
            if not wait_for_response:
                return json.dumps({
                    "status": "sent",
                    "message_id": message_id
                })
            
            # Wait for response
            response = await self._wait_for_response(project_id, from_session, to_session, message_id, timeout)
            if response:
                return json.dumps({
                    "status": "received",
                    "response": response
                })
            else:
                return json.dumps({
                    "status": "timeout",
                    "error": f"No response received within {timeout} seconds"
                })
        
        @self.server.tool()
        async def check_messages(project_id: str, session_name: str) -> str:
            """Check for messages sent to this agent."""
            messages_key = self._get_key(project_id, "messages", session_name)
            
            # Get all messages
            messages_raw = await self.redis_client.lrange(messages_key, 0, -1)
            messages = [json.loads(msg) for msg in messages_raw]
            
            # Clear the queue
            await self.redis_client.delete(messages_key)
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            return json.dumps(messages, indent=2)
        
        @self.server.tool()
        async def respond_to_query(
            project_id: str,
            from_session: str,
            to_session: str,
            message_id: str,
            response: str
        ) -> str:
            """Respond to a query from another agent."""
            response_msg = {
                "id": f"response-{message_id}",
                "from": from_session,
                "type": "response",
                "response_to": message_id,
                "content": response,
                "timestamp": datetime.now().isoformat()
            }
            
            messages_key = self._get_key(project_id, "messages", to_session)
            await self.redis_client.rpush(messages_key, json.dumps(response_msg))
            
            # Update heartbeat
            await self._update_heartbeat(project_id, from_session)
            
            return json.dumps({
                "status": "response_sent",
                "to": to_session
            })
        
        @self.server.tool()
        async def announce_file_change(
            project_id: str,
            session_name: str,
            file_path: str,
            change_type: str,
            description: str
        ) -> str:
            """Announce intention to modify a file."""
            locks_key = self._get_key(project_id, "locks")
            
            # Check for existing lock
            existing_lock = await self.redis_client.hget(locks_key, file_path)
            if existing_lock:
                lock_info = json.loads(existing_lock)
                if lock_info["session"] != session_name:
                    return json.dumps({
                        "status": "conflict",
                        "error": f"File is locked by {lock_info['session']}",
                        "lock_info": lock_info,
                        "suggestion": "Query that agent about their progress or wait"
                    })
            
            # Create lock
            lock_data = {
                "session": session_name,
                "locked_at": datetime.now().isoformat(),
                "change_type": change_type,
                "description": description
            }
            
            await self.redis_client.hset(locks_key, file_path, json.dumps(lock_data))
            
            # Add to recent changes
            changes_key = self._get_key(project_id, "recent_changes")
            change_record = {
                "session": session_name,
                "file_path": file_path,
                "change_type": change_type,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
            await self.redis_client.lpush(changes_key, json.dumps(change_record))
            await self.redis_client.ltrim(changes_key, 0, 99)  # Keep last 100
            
            # Broadcast
            await self._broadcast_event(project_id, {
                "type": "file_change_announced",
                "session": session_name,
                "file_path": file_path,
                "change_type": change_type,
                "description": description
            }, exclude=session_name)
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            logger.info(f"Agent {session_name} locked {file_path} in project {project_id}")
            
            return json.dumps({
                "status": "locked",
                "file_path": file_path,
                "message": "File locked successfully. Remember to release when done."
            })
        
        @self.server.tool()
        async def release_file_lock(
            project_id: str,
            session_name: str,
            file_path: str
        ) -> str:
            """Release a file lock."""
            locks_key = self._get_key(project_id, "locks")
            
            existing_lock = await self.redis_client.hget(locks_key, file_path)
            if not existing_lock:
                return json.dumps({
                    "status": "not_locked",
                    "message": "File was not locked"
                })
            
            lock_info = json.loads(existing_lock)
            if lock_info["session"] != session_name:
                return json.dumps({
                    "status": "error",
                    "error": f"File is locked by {lock_info['session']}, not you"
                })
            
            await self.redis_client.hdel(locks_key, file_path)
            
            # Broadcast
            await self._broadcast_event(project_id, {
                "type": "file_lock_released",
                "session": session_name,
                "file_path": file_path
            }, exclude=session_name)
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            logger.info(f"Agent {session_name} released lock on {file_path}")
            
            return json.dumps({
                "status": "released",
                "file_path": file_path
            })
        
        @self.server.tool()
        async def register_interface(
            project_id: str,
            session_name: str,
            interface_name: str,
            definition: str,
            file_path: Optional[str] = None
        ) -> str:
            """Register a shared interface or type definition."""
            interfaces_key = self._get_key(project_id, "interfaces")
            
            interface_data = {
                "definition": definition,
                "registered_by": session_name,
                "file_path": file_path,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.hset(interfaces_key, interface_name, json.dumps(interface_data))
            
            # Broadcast
            await self._broadcast_event(project_id, {
                "type": "interface_registered",
                "session": session_name,
                "interface_name": interface_name,
                "definition": definition
            }, exclude=session_name)
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            logger.info(f"Agent {session_name} registered interface {interface_name}")
            
            return json.dumps({
                "status": "registered",
                "interface_name": interface_name,
                "message": "Interface registered and available to all agents"
            })
        
        @self.server.tool()
        async def query_interface(project_id: str, interface_name: str) -> str:
            """Get a registered interface definition."""
            interfaces_key = self._get_key(project_id, "interfaces")
            
            interface_data = await self.redis_client.hget(interfaces_key, interface_name)
            if not interface_data:
                # Try to find similar names
                all_interfaces = await self.redis_client.hkeys(interfaces_key)
                similar = [name for name in all_interfaces 
                          if interface_name.lower() in name.lower()]
                
                return json.dumps({
                    "status": "not_found",
                    "error": f"Interface {interface_name} not found",
                    "similar": similar
                })
            
            return json.dumps(json.loads(interface_data), indent=2)
        
        @self.server.tool()
        async def list_interfaces(project_id: str) -> str:
            """List all registered interfaces in the project."""
            interfaces_key = self._get_key(project_id, "interfaces")
            interfaces_data = await self.redis_client.hgetall(interfaces_key)
            
            interfaces = {}
            for name, data in interfaces_data.items():
                interfaces[name] = json.loads(data)
            
            return json.dumps(interfaces, indent=2)
        
        @self.server.tool()
        async def get_recent_changes(project_id: str, limit: int = 20) -> str:
            """Get recent file changes in the project."""
            changes_key = self._get_key(project_id, "recent_changes")
            changes_raw = await self.redis_client.lrange(changes_key, 0, limit - 1)
            
            changes = [json.loads(change) for change in changes_raw]
            
            return json.dumps(changes, indent=2)
        
        @self.server.tool()
        async def broadcast_message(
            project_id: str,
            session_name: str,
            message_type: str,
            content: str
        ) -> str:
            """Broadcast a message to all agents in the project."""
            message = {
                "from": session_name,
                "type": "broadcast",
                "message_type": message_type,
                "content": content,
                "timestamp": datetime.now().isoformat()
            }
            
            # Get all agents
            agents_key = self._get_key(project_id, "agents")
            all_agents = await self.redis_client.hkeys(agents_key)
            
            # Send to all other agents
            count = 0
            for agent_session in all_agents:
                if agent_session != session_name:
                    messages_key = self._get_key(project_id, "messages", agent_session)
                    await self.redis_client.rpush(messages_key, json.dumps(message))
                    count += 1
            
            # Update heartbeat
            await self._update_heartbeat(project_id, session_name)
            
            return json.dumps({
                "status": "broadcast_sent",
                "recipients": count
            })
        
        @self.server.tool()
        async def mark_task_completed(project_id: str, session_name: str, task_id: str) -> str:
            """
            Mark a task as completed. This signals to the orchestrator that the agent
            has finished its work and the session can be terminated.
            
            Args:
                project_id: Project identifier
                session_name: Agent's session name
                task_id: Task ID that was completed
            """
            # Store completion status
            completion_key = self._get_key(project_id, "completed_tasks")
            completion_data = {
                "task_id": task_id,
                "session_name": session_name,
                "completed_at": datetime.now().isoformat()
            }
            await self.redis_client.hset(completion_key, task_id, json.dumps(completion_data))
            
            # Also mark in agent data
            agents_key = self._get_key(project_id, "agents")
            agent_data = await self.redis_client.hget(agents_key, session_name)
            if agent_data:
                agent_info = json.loads(agent_data)
                agent_info["status"] = "completed"
                await self.redis_client.hset(agents_key, session_name, json.dumps(agent_info))
            
            # Notify orchestrator by creating a status file
            import os
            status_file = f"/tmp/splitmind-status/{session_name}.status"
            try:
                with open(status_file, 'w') as f:
                    f.write("COMPLETED\n")
            except Exception as e:
                logger.error(f"Failed to write status file: {e}")
            
            logger.info(f"Task {task_id} marked as completed by {session_name}")
            
            return json.dumps({
                "status": "success",
                "message": f"Task {task_id} marked as completed"
            })
        
        @self.server.tool()
        async def unregister_agent(project_id: str, session_name: str) -> str:
            """Unregister an agent when task is complete."""
            agents_key = self._get_key(project_id, "agents")
            
            if not await self.redis_client.hexists(agents_key, session_name):
                return json.dumps({
                    "status": "not_found",
                    "error": "Agent not registered"
                })
            
            # Get agent data before removing
            agent_data = await self.redis_client.hget(agents_key, session_name)
            agent_info = json.loads(agent_data) if agent_data else {}
            
            # Get final todo status
            todos_key = self._get_key(project_id, "todos", session_name)
            todos_raw = await self.redis_client.lrange(todos_key, 0, -1)
            todos = [json.loads(todo) for todo in todos_raw]
            
            todo_summary = {
                "total": len(todos),
                "completed": len([t for t in todos if t["status"] == "completed"]),
                "pending": len([t for t in todos if t["status"] == "pending"]),
                "in_progress": len([t for t in todos if t["status"] == "in_progress"])
            }
            
            # Clean up
            await self._cleanup_dead_agent(project_id, session_name)
            
            # Broadcast departure with summary
            await self._broadcast_event(project_id, {
                "type": "agent_left",
                "session": session_name,
                "task_id": agent_info.get("task_id"),
                "todo_summary": todo_summary
            })
            
            logger.info(f"Agent {session_name} unregistered from project {project_id}")
            
            return json.dumps({
                "status": "unregistered",
                "todo_summary": todo_summary,
                "message": f"Successfully unregistered. Completed {todo_summary['completed']}/{todo_summary['total']} todos."
            })
    
    async def _wait_for_response(self, project_id: str, from_session: str, to_session: str, 
                                 message_id: str, timeout: int):
        """Wait for a response to a specific message"""
        start_time = asyncio.get_event_loop().time()
        messages_key = self._get_key(project_id, "messages", to_session)
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check for response in Redis
            messages_raw = await self.redis_client.lrange(messages_key, 0, -1)
            
            for i, msg_str in enumerate(messages_raw):
                msg = json.loads(msg_str)
                if (msg.get("type") == "response" and 
                    msg.get("response_to") == message_id and
                    msg.get("from") == from_session):
                    # Remove this specific message
                    await self.redis_client.lrem(messages_key, 1, msg_str)
                    return msg["content"]
            
            await asyncio.sleep(0.5)
        
        return None
    
    async def _broadcast_event(self, project_id: str, event: dict, exclude: Optional[str] = None):
        """Broadcast an event to all agents in a project"""
        event["timestamp"] = datetime.now().isoformat()
        
        agents_key = self._get_key(project_id, "agents")
        all_agents = await self.redis_client.hkeys(agents_key)
        
        for agent_session in all_agents:
            if agent_session != exclude:
                messages_key = self._get_key(project_id, "messages", agent_session)
                await self.redis_client.rpush(messages_key, json.dumps(event))
    
    async def run(self):
        """Run the MCP server"""
        logger.info("Starting SplitMind Agent Communication Server with Redis")
        
        await self.initialize()
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options()
                )
        finally:
            await self.cleanup()


@asynccontextmanager
async def run_server():
    """Context manager for running the server"""
    server = AgentCommunicationServer()
    try:
        await server.run()
    finally:
        await server.cleanup()


if __name__ == "__main__":
    asyncio.run(run_server())