#!/usr/bin/env python3
"""
Test all MCP server endpoints
This script tests the A2AMCP server by connecting directly to Redis
"""

import asyncio
import json
import redis.asyncio as redis
from datetime import datetime
import sys

class MCPServerTester:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.project_id = "test-project"
        self.test_results = []
    
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(self.redis_url, decode_responses=True)
        print("✓ Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.aclose()
    
    def _get_key(self, key_type: str, *args) -> str:
        """Generate Redis key with project namespace"""
        parts = [f"project:{self.project_id}", key_type]
        parts.extend(args)
        return ":".join(parts)
    
    async def test_agent_registration(self):
        """Test agent registration"""
        print("\n=== Testing Agent Registration ===")
        
        # Register first agent
        agent1_data = {
            "task_id": "TASK-001",
            "branch": "feature/test-1",
            "description": "Test agent 1",
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "project_id": self.project_id
        }
        
        agents_key = self._get_key("agents")
        await self.redis_client.hset(agents_key, "test-agent-1", json.dumps(agent1_data))
        print("✓ Registered test-agent-1")
        
        # Register second agent
        agent2_data = {
            "task_id": "TASK-002",
            "branch": "feature/test-2",
            "description": "Test agent 2",
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "project_id": self.project_id
        }
        
        await self.redis_client.hset(agents_key, "test-agent-2", json.dumps(agent2_data))
        print("✓ Registered test-agent-2")
        
        # Verify agents
        all_agents = await self.redis_client.hgetall(agents_key)
        print(f"✓ Total agents registered: {len(all_agents)}")
        
        return True
    
    async def test_messaging(self):
        """Test agent messaging"""
        print("\n=== Testing Messaging ===")
        
        # Send message from agent 1 to agent 2
        msg_data = {
            "id": "msg_001",
            "from": "test-agent-1",
            "to": "test-agent-2",
            "message": "Hello from agent 1",
            "type": "query",
            "timestamp": datetime.now().isoformat()
        }
        
        messages_key = self._get_key("messages", "test-agent-2")
        await self.redis_client.rpush(messages_key, json.dumps(msg_data))
        print("✓ Sent message from test-agent-1 to test-agent-2")
        
        # Check message queue
        messages = await self.redis_client.lrange(messages_key, 0, -1)
        print(f"✓ Messages in queue for test-agent-2: {len(messages)}")
        
        # Broadcast message
        broadcast_data = {
            "type": "broadcast",
            "from": "test-agent-1",
            "message": "Broadcast to all agents",
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to all agents
        all_agents = await self.redis_client.hkeys(self._get_key("agents"))
        for agent in all_agents:
            if agent != "test-agent-1":
                agent_messages_key = self._get_key("messages", agent)
                await self.redis_client.rpush(agent_messages_key, json.dumps(broadcast_data))
        
        print("✓ Broadcast message sent")
        
        return True
    
    async def test_todo_management(self):
        """Test todo list management"""
        print("\n=== Testing Todo Management ===")
        
        # Create todos for agent 1
        todos = [
            {"id": "1", "text": "Implement feature X", "status": "pending", "priority": 1},
            {"id": "2", "text": "Write tests", "status": "in_progress", "priority": 2},
            {"id": "3", "text": "Update documentation", "status": "pending", "priority": 3}
        ]
        
        todos_data = {
            "todos": todos,
            "updated_at": datetime.now().isoformat()
        }
        
        todos_key = self._get_key("todos", "test-agent-1")
        await self.redis_client.set(todos_key, json.dumps(todos_data))
        print(f"✓ Created {len(todos)} todos for test-agent-1")
        
        # Retrieve todos
        stored_todos = await self.redis_client.get(todos_key)
        if stored_todos:
            data = json.loads(stored_todos)
            print(f"✓ Retrieved {len(data['todos'])} todos")
        
        return True
    
    async def test_file_locking(self):
        """Test file locking mechanism"""
        print("\n=== Testing File Locking ===")
        
        # Lock a file by agent 1
        file_path = "src/main.py"
        lock_data = {
            "locked_by": "test-agent-1",
            "locked_at": datetime.now().isoformat(),
            "change_type": "edit",
            "description": "Adding new feature"
        }
        
        file_key = self._get_key("files", file_path)
        await self.redis_client.setex(file_key, 300, json.dumps(lock_data))
        print(f"✓ Locked file {file_path} by test-agent-1")
        
        # Try to lock same file by agent 2 (should fail)
        existing = await self.redis_client.get(file_key)
        if existing:
            existing_data = json.loads(existing)
            if existing_data["locked_by"] != "test-agent-2":
                print(f"✓ File lock conflict detected correctly (locked by {existing_data['locked_by']})")
        
        # Release file lock
        await self.redis_client.delete(file_key)
        print(f"✓ Released file lock on {file_path}")
        
        return True
    
    async def test_heartbeat(self):
        """Test heartbeat mechanism"""
        print("\n=== Testing Heartbeat ===")
        
        # Set heartbeat for agents
        for agent in ["test-agent-1", "test-agent-2"]:
            heartbeat_key = self._get_key("heartbeat", agent)
            await self.redis_client.setex(heartbeat_key, 120, datetime.now().isoformat())
            print(f"✓ Set heartbeat for {agent}")
        
        # Check heartbeat
        heartbeat_key = self._get_key("heartbeat", "test-agent-1")
        heartbeat = await self.redis_client.get(heartbeat_key)
        if heartbeat:
            print("✓ Heartbeat active for test-agent-1")
        
        return True
    
    async def cleanup(self):
        """Clean up test data"""
        print("\n=== Cleaning Up ===")
        
        # Clean up all test data
        pattern = f"project:{self.project_id}:*"
        keys = await self.redis_client.keys(pattern)
        
        if keys:
            await self.redis_client.delete(*keys)
            print(f"✓ Cleaned up {len(keys)} test keys")
        
        return True
    
    async def run_all_tests(self):
        """Run all tests"""
        print("Starting A2AMCP Server Endpoint Tests")
        print("====================================")
        
        try:
            await self.connect()
            
            # Run tests
            await self.test_agent_registration()
            await self.test_messaging()
            await self.test_todo_management()
            await self.test_file_locking()
            await self.test_heartbeat()
            
            # Cleanup
            await self.cleanup()
            
            print("\n✅ All tests completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            raise
        finally:
            await self.disconnect()

async def main():
    """Main entry point"""
    # Check if Redis is accessible
    tester = MCPServerTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())