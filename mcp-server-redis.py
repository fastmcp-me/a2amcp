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
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import redis.asyncio as redis

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentCommunicationServer:
    """MCP server for agent-to-agent communication with Redis backend"""
    
    def __init__(self):
        self.server = Server("splitmind-mcp-server")
        self.redis_client = None
        self.heartbeat_timeout = int(os.getenv("HEARTBEAT_TIMEOUT", "120"))
        self._heartbeat_task = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools"""
            return [
                Tool(
                    name="register_agent",
                    description="Register an agent for a specific project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string", "description": "Unique project identifier"},
                            "session_name": {"type": "string", "description": "Unique tmux session name"},
                            "task_id": {"type": "string", "description": "The task ID this agent is working on"},
                            "branch": {"type": "string", "description": "Git branch name for this task"},
                            "description": {"type": "string", "description": "Brief description of the task"}
                        },
                        "required": ["project_id", "session_name", "task_id", "branch", "description"]
                    }
                ),
                Tool(
                    name="unregister_agent",
                    description="Unregister an agent when its task is complete",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"}
                        },
                        "required": ["project_id", "session_name"]
                    }
                ),
                Tool(
                    name="get_active_agents",
                    description="Get all active agents for a project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"}
                        },
                        "required": ["project_id"]
                    }
                ),
                Tool(
                    name="heartbeat",
                    description="Update agent heartbeat to indicate it's still active",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"}
                        },
                        "required": ["project_id", "session_name"]
                    }
                ),
                Tool(
                    name="send_message",
                    description="Send a message to another agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "from_session": {"type": "string"},
                            "to_session": {"type": "string"},
                            "message": {"type": "string"},
                            "message_type": {"type": "string", "enum": ["query", "broadcast"]}
                        },
                        "required": ["project_id", "from_session", "to_session", "message"]
                    }
                ),
                Tool(
                    name="get_messages",
                    description="Get pending messages for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"}
                        },
                        "required": ["project_id", "session_name"]
                    }
                ),
                Tool(
                    name="update_todo_list",
                    description="Update the todo list for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"},
                            "todos": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "string"},
                                        "text": {"type": "string"},
                                        "status": {"type": "string"},
                                        "priority": {"type": "integer"}
                                    }
                                }
                            }
                        },
                        "required": ["project_id", "session_name", "todos"]
                    }
                ),
                Tool(
                    name="get_todo_list",
                    description="Get the current todo list for an agent",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"}
                        },
                        "required": ["project_id", "session_name"]
                    }
                ),
                Tool(
                    name="register_file_change",
                    description="Register that an agent is changing a file",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"},
                            "file_path": {"type": "string"},
                            "change_type": {"type": "string"},
                            "description": {"type": "string"}
                        },
                        "required": ["project_id", "session_name", "file_path", "change_type"]
                    }
                ),
                Tool(
                    name="release_file",
                    description="Release a file lock",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "session_name": {"type": "string"},
                            "file_path": {"type": "string"}
                        },
                        "required": ["project_id", "session_name", "file_path"]
                    }
                ),
                Tool(
                    name="check_file_conflicts",
                    description="Check if any files have conflicts",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "project_id": {"type": "string"},
                            "file_paths": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["project_id", "file_paths"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if name == "register_agent":
                    result = await self._register_agent(**arguments)
                elif name == "unregister_agent":
                    result = await self._unregister_agent(**arguments)
                elif name == "get_active_agents":
                    result = await self._get_active_agents(**arguments)
                elif name == "heartbeat":
                    result = await self._heartbeat(**arguments)
                elif name == "send_message":
                    result = await self._send_message(**arguments)
                elif name == "get_messages":
                    result = await self._get_messages(**arguments)
                elif name == "update_todo_list":
                    result = await self._update_todo_list(**arguments)
                elif name == "get_todo_list":
                    result = await self._get_todo_list(**arguments)
                elif name == "register_file_change":
                    result = await self._register_file_change(**arguments)
                elif name == "release_file":
                    result = await self._release_file(**arguments)
                elif name == "check_file_conflicts":
                    result = await self._check_file_conflicts(**arguments)
                else:
                    result = f"Unknown tool: {name}"
                
                return [TextContent(type="text", text=json.dumps(result))]
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    async def initialize(self):
        """Initialize Redis connection"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = await redis.from_url(redis_url, decode_responses=True)
        
        # Start heartbeat monitor
        self._heartbeat_task = asyncio.create_task(self._monitor_heartbeats())
        
        logger.info("Redis connection established")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.aclose()
    
    def _get_key(self, project_id: str, key_type: str, *args) -> str:
        """Generate Redis key with project namespace"""
        parts = [f"project:{project_id}", key_type]
        parts.extend(args)
        return ":".join(parts)
    
    async def _update_heartbeat(self, project_id: str, session_name: str):
        """Update agent heartbeat timestamp"""
        heartbeat_key = self._get_key(project_id, "heartbeat", session_name)
        await self.redis_client.setex(
            heartbeat_key,
            self.heartbeat_timeout,
            datetime.now().isoformat()
        )
    
    async def _monitor_heartbeats(self):
        """Monitor agent heartbeats and clean up stale agents"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Get all project keys
                project_keys = await self.redis_client.keys("project:*:agents")
                
                for agents_key in project_keys:
                    # Extract project_id from key
                    parts = agents_key.split(":")
                    project_id = parts[1]
                    
                    # Get all agents in this project
                    agents = await self.redis_client.hgetall(agents_key)
                    
                    for session_name, agent_data_str in agents.items():
                        heartbeat_key = self._get_key(project_id, "heartbeat", session_name)
                        heartbeat = await self.redis_client.get(heartbeat_key)
                        
                        if not heartbeat:
                            # No heartbeat found, agent is stale
                            logger.warning(f"Removing stale agent {session_name} from project {project_id}")
                            await self._cleanup_agent(project_id, session_name)
                            
                            # Notify other agents
                            await self._broadcast_event(project_id, {
                                "type": "agent_timeout",
                                "session_name": session_name,
                                "reason": "heartbeat_timeout"
                            })
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
    
    async def _cleanup_agent(self, project_id: str, session_name: str):
        """Clean up all data for a disconnected agent"""
        # Remove from agents hash
        agents_key = self._get_key(project_id, "agents")
        await self.redis_client.hdel(agents_key, session_name)
        
        # Clean up message queue
        messages_key = self._get_key(project_id, "messages", session_name)
        await self.redis_client.delete(messages_key)
        
        # Clean up todos
        todos_key = self._get_key(project_id, "todos", session_name)
        await self.redis_client.delete(todos_key)
    
    # Tool implementations
    async def _register_agent(self, project_id: str, session_name: str, task_id: str,
                             branch: str, description: str) -> Dict[str, Any]:
        """Register an agent for a specific project"""
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
        await self.redis_client.delete(todos_key)
        
        # Notify other agents in the project
        await self._broadcast_event(project_id, {
            "type": "agent_joined",
            "session_name": session_name,
            "description": description
        }, exclude=session_name)
        
        # Get other active agents
        all_agents = await self.redis_client.hgetall(agents_key)
        other_agents = []
        for other_session, agent_str in all_agents.items():
            if other_session != session_name:
                other_agents.append({
                    "session_name": other_session,
                    **json.loads(agent_str)
                })
        
        return {
            "status": "success",
            "session_name": session_name,
            "other_agents": other_agents
        }
    
    async def _unregister_agent(self, project_id: str, session_name: str) -> Dict[str, Any]:
        """Unregister an agent when its task is complete"""
        await self._cleanup_agent(project_id, session_name)
        
        # Notify other agents
        await self._broadcast_event(project_id, {
            "type": "agent_left",
            "session_name": session_name,
            "reason": "task_complete"
        })
        
        return {"status": "success", "message": f"Agent {session_name} unregistered"}
    
    async def _get_active_agents(self, project_id: str) -> Dict[str, Any]:
        """Get all active agents for a project"""
        agents_key = self._get_key(project_id, "agents")
        all_agents = await self.redis_client.hgetall(agents_key)
        
        active_agents = []
        for session_name, agent_str in all_agents.items():
            agent_data = json.loads(agent_str)
            agent_data["session_name"] = session_name
            active_agents.append(agent_data)
        
        return {"agents": active_agents}
    
    async def _heartbeat(self, project_id: str, session_name: str) -> Dict[str, Any]:
        """Update agent heartbeat"""
        await self._update_heartbeat(project_id, session_name)
        return {"status": "success", "timestamp": datetime.now().isoformat()}
    
    async def _send_message(self, project_id: str, from_session: str, to_session: str,
                           message: str, message_type: str = "query") -> Dict[str, Any]:
        """Send a message to another agent"""
        msg_data = {
            "id": f"{from_session}_{int(time.time()*1000)}",
            "from": from_session,
            "to": to_session,
            "message": message,
            "type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        
        if message_type == "broadcast":
            # Send to all agents except sender
            await self._broadcast_event(project_id, msg_data, exclude=from_session)
            return {"status": "success", "broadcast": True}
        else:
            # Send to specific agent
            messages_key = self._get_key(project_id, "messages", to_session)
            await self.redis_client.rpush(messages_key, json.dumps(msg_data))
            return {"status": "success", "message_id": msg_data["id"]}
    
    async def _get_messages(self, project_id: str, session_name: str) -> Dict[str, Any]:
        """Get pending messages for an agent"""
        messages_key = self._get_key(project_id, "messages", session_name)
        
        # Get all messages
        messages_raw = await self.redis_client.lrange(messages_key, 0, -1)
        
        # Clear the queue
        await self.redis_client.delete(messages_key)
        
        # Parse messages
        messages = [json.loads(msg) for msg in messages_raw]
        
        return {"messages": messages}
    
    async def _update_todo_list(self, project_id: str, session_name: str, 
                               todos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update the todo list for an agent"""
        todos_key = self._get_key(project_id, "todos", session_name)
        
        # Store todos
        todos_data = {
            "todos": todos,
            "updated_at": datetime.now().isoformat()
        }
        await self.redis_client.set(todos_key, json.dumps(todos_data))
        
        # Notify other agents about todo update
        await self._broadcast_event(project_id, {
            "type": "todo_update",
            "session_name": session_name,
            "todo_count": len(todos)
        }, exclude=session_name)
        
        return {"status": "success", "todo_count": len(todos)}
    
    async def _get_todo_list(self, project_id: str, session_name: str) -> Dict[str, Any]:
        """Get the current todo list for an agent"""
        todos_key = self._get_key(project_id, "todos", session_name)
        todos_str = await self.redis_client.get(todos_key)
        
        if todos_str:
            todos_data = json.loads(todos_str)
            return todos_data
        else:
            return {"todos": [], "updated_at": None}
    
    async def _register_file_change(self, project_id: str, session_name: str,
                                   file_path: str, change_type: str,
                                   description: str = "") -> Dict[str, Any]:
        """Register that an agent is changing a file"""
        file_key = self._get_key(project_id, "files", file_path)
        
        # Check if file is already locked
        existing = await self.redis_client.get(file_key)
        if existing:
            existing_data = json.loads(existing)
            if existing_data["locked_by"] != session_name:
                return {
                    "status": "conflict",
                    "locked_by": existing_data["locked_by"],
                    "locked_at": existing_data["locked_at"]
                }
        
        # Lock the file
        lock_data = {
            "locked_by": session_name,
            "locked_at": datetime.now().isoformat(),
            "change_type": change_type,
            "description": description
        }
        
        # Set with expiration (5 minutes)
        await self.redis_client.setex(file_key, 300, json.dumps(lock_data))
        
        # Notify other agents
        await self._broadcast_event(project_id, {
            "type": "file_locked",
            "session_name": session_name,
            "file_path": file_path,
            "change_type": change_type
        }, exclude=session_name)
        
        return {"status": "success", "file_path": file_path}
    
    async def _release_file(self, project_id: str, session_name: str,
                           file_path: str) -> Dict[str, Any]:
        """Release a file lock"""
        file_key = self._get_key(project_id, "files", file_path)
        
        # Check if the agent owns the lock
        existing = await self.redis_client.get(file_key)
        if existing:
            existing_data = json.loads(existing)
            if existing_data["locked_by"] == session_name:
                await self.redis_client.delete(file_key)
                
                # Notify other agents
                await self._broadcast_event(project_id, {
                    "type": "file_released",
                    "session_name": session_name,
                    "file_path": file_path
                }, exclude=session_name)
                
                return {"status": "success", "file_path": file_path}
        
        return {"status": "error", "message": "File not locked by this agent"}
    
    async def _check_file_conflicts(self, project_id: str, 
                                   file_paths: List[str]) -> Dict[str, Any]:
        """Check if any files have conflicts"""
        conflicts = []
        
        for file_path in file_paths:
            file_key = self._get_key(project_id, "files", file_path)
            lock_data = await self.redis_client.get(file_key)
            
            if lock_data:
                conflict = json.loads(lock_data)
                conflict["file_path"] = file_path
                conflicts.append(conflict)
        
        return {"conflicts": conflicts}
    
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


async def main():
    """Main entry point"""
    server = AgentCommunicationServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())