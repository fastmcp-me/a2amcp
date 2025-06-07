# A2AMCP Architecture

## Overview

A2AMCP (Agent-to-Agent Model Context Protocol) is a distributed communication system that enables AI agents to coordinate while working on parallel development tasks. It provides persistent state management, conflict prevention, and real-time messaging through a centralized MCP server backed by Redis.
    
## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        User's Machine                         │
│                                                               │
│  ┌─────────────────┐        ┌──────────────────────────┐    │
│  │   Orchestrator   │        │     Docker Network        │    │
│  │                 │        │                           │    │
│  │  - Task Manager │        │  ┌───────────────────┐  │    │
│  │  - Agent Spawner│        │  │   A2AMCP Server   │  │    │
│  │  - Monitor      │        │  │                   │  │    │
│  └─────────────────┘        │  │  - MCP Handler    │  │    │
│                             │  │  - Message Router  │  │    │
│         Spawns              │  │  - State Manager   │  │    │
│            ↓                │  │                   │  │    │
│                             │  └────────┬──────────┘  │    │
│  ┌─────────────────────┐    │           │             │    │
│  │   tmux sessions     │    │           │             │    │
│  │                     │    │  ┌────────┴──────────┐  │    │
│  │  ┌──────────────┐  │    │  │   Redis Server    │  │    │
│  │  │ Agent task-1 │←─┼────┼─→│                   │  │    │
│  │  │ (Claude Code)│  │    │  │  - Persistence    │  │    │
│  │  └──────────────┘  │    │  │  - Pub/Sub        │  │    │
│  │                     │    │  │  - Namespacing    │  │    │
│  │  ┌──────────────┐  │    │  │                   │  │    │
│  │  │ Agent task-2 │←─┼────┼─→│  project:app:*    │  │    │
│  │  │ (Claude Code)│  │    │  │  project:web:*    │  │    │
│  │  └──────────────┘  │    │  │                   │  │    │
│  │                     │    │  └───────────────────┘  │    │
│  │  ┌──────────────┐  │    │                           │    │
│  │  │ Agent task-N │←─┼────┼───────────────────────────┘    │
│  │  │ (Claude Code)│  │    │                                │
│  │  └──────────────┘  │    │                                │
│  └─────────────────────┘    │                                │
│                             │                                │
└──────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MCP Server

The central communication hub implemented in Python:

```python
class AgentCommunicationServer:
    def __init__(self, redis_url):
        self.server = Server("a2amcp")
        self.redis_client = redis.from_url(redis_url)
        self._setup_tools()  # Register MCP tools
```

**Responsibilities:**
- Handle MCP tool calls from agents
- Route messages between agents
- Manage agent lifecycle
- Monitor heartbeats
- Clean up dead agents

**Key Features:**
- Stateless design (all state in Redis)
- Async/await for concurrent operations
- Automatic cleanup via heartbeat monitoring
- Project namespace isolation

### 2. Redis Backend

Provides persistent storage and pub/sub messaging:

**Data Structure:**
```
redis-server/
├── project:{project_id}:agents          # Hash: agent registry
├── project:{project_id}:heartbeat:{id}  # String: last heartbeat
├── project:{project_id}:locks           # Hash: file locks
├── project:{project_id}:interfaces      # Hash: shared types
├── project:{project_id}:todos:{id}      # List: agent todos
├── project:{project_id}:messages:{id}   # List: message queue
└── project:{project_id}:recent_changes  # List: change history
```

**Benefits:**
- Persistence across restarts
- Horizontal scalability
- Built-in pub/sub for events
- Atomic operations
- TTL for automatic cleanup

### 3. AI Agents

Individual Claude Code instances running in tmux sessions:

**Agent Lifecycle:**
```
Start → Register → Heartbeat Loop → Work → Unregister
         ↓                ↓                    ↑
         └── Check Messages ←─────────────────┘
```

**Agent Capabilities:**
- Register with project and task info
- Maintain heartbeat for liveness
- Create and update todo lists
- Lock files before modification
- Share interfaces and contracts
- Query other agents
- Broadcast messages

### 4. Communication Protocol

#### Message Types

1. **Direct Query**
   ```
   Agent A → MCP Server → Redis → Agent B's Queue
                                        ↓
   Agent A ← MCP Server ← Redis ← Agent B Response
   ```

2. **Broadcast**
   ```
   Agent A → MCP Server → Redis → All Other Agents' Queues
   ```

3. **Event Notification**
   ```
   System Event → Redis Pub/Sub → Subscribed Agents
   ```

#### Message Format
```json
{
  "id": "unique-message-id",
  "from": "task-001",
  "type": "query|broadcast|response|event",
  "content": "message content",
  "timestamp": "ISO-8601",
  "metadata": {}
}
```

## Key Design Decisions

### 1. MCP vs HTTP

**Why MCP:**
- Native integration with Claude Code
- No need for HTTP servers per agent
- Simpler security model
- Direct tool calls from AI context

**Trade-offs:**
- Limited to MCP-compatible agents
- Less flexibility than HTTP
- Requires MCP runtime

### 2. Centralized vs Distributed

**Why Centralized Server:**
- Simpler consistency model
- Easier debugging
- Single point for monitoring
- Reduced network complexity

**Trade-offs:**
- Single point of failure (mitigated by Redis persistence)
- Potential bottleneck (mitigated by async operations)

### 3. Redis vs Other Storage

**Why Redis:**
- In-memory performance
- Built-in data structures
- Pub/sub capabilities
- Persistence options
- Wide language support

**Alternatives Considered:**
- PostgreSQL: Too heavy for message queuing
- RabbitMQ: Overkill for our use case
- In-memory only: No persistence

### 4. Project Namespacing

**Implementation:**
```
project:{project_id}:{resource_type}:{resource_id}
```

**Benefits:**
- Complete isolation between projects
- Easy cleanup of project data
- Parallel project support
- Clear data organization

## Scalability Considerations

### Current Limits

- **Agents per project**: 100+ (tested)
- **Messages per second**: 1000+
- **File operations**: No hard limit
- **Storage**: Limited by Redis memory

### Scaling Strategies

1. **Vertical Scaling**
   - Increase Redis memory
   - Upgrade server CPU/RAM
   - Optimize message processing

2. **Horizontal Scaling**
   - Redis Cluster for data sharding
   - Multiple MCP servers with load balancing
   - Read replicas for queries

3. **Performance Optimizations**
   - Message batching
   - Caching frequent queries
   - Lazy loading of todos
   - Compression for large messages

## Security Model

### Current Security

1. **Network Isolation**
   - Docker network isolation
   - Local-only by default
   - No external exposure

2. **Project Isolation**
   - Namespace separation
   - No cross-project access
   - Project-specific operations

### Future Security Enhancements

1. **Authentication**
   - API key per project
   - JWT tokens for agents
   - OAuth integration

2. **Authorization**
   - Role-based access
   - Operation permissions
   - Resource quotas

3. **Encryption**
   - TLS for network traffic
   - Encrypted storage
   - Secure key management

## Fault Tolerance

### Failure Scenarios

1. **Agent Crash**
   - Detected via heartbeat timeout
   - Automatic cleanup (locks, registry)
   - Other agents continue

2. **MCP Server Crash**
   - State preserved in Redis
   - Agents reconnect on restart
   - Messages queued in Redis

3. **Redis Crash**
   - AOF persistence for recovery
   - RDB snapshots for backup
   - Potential data loss window

### Recovery Mechanisms

1. **Heartbeat Monitoring**
   ```python
   async def _heartbeat_monitor(self):
       while True:
           check_all_heartbeats()
           cleanup_dead_agents()
           await asyncio.sleep(30)
   ```

2. **Lock Cleanup**
   - Automatic on agent death
   - Manual unlock available
   - Timeout-based release (future)

3. **Message Replay**
   - Messages persist until acknowledged
   - At-least-once delivery
   - Idempotent operations recommended

## Integration Points

### 1. Orchestrator Integration

```python
from a2amcp import A2AMCPClient, Project, AgentSpawner

client = A2AMCPClient("localhost:5000")
project = Project(client, "my-app")
spawner = AgentSpawner(project)

# Spawn agents with A2AMCP awareness
sessions = await spawner.spawn_multiple(tasks, worktree_base)
```

### 2. Monitoring Integration

- Prometheus metrics (planned)
- Health check endpoints
- WebSocket for real-time updates
- REST API for dashboards

### 3. CI/CD Integration

- Pre-flight checks for conflicts
- Automated testing with mock agents
- Performance benchmarks
- Integration test suites

## Future Architecture Evolution

### 1. Event Sourcing
- Complete audit trail
- Time-travel debugging
- Replay capabilities

### 2. GraphQL API
- Flexible queries
- Real-time subscriptions
- Better client efficiency

### 3. Plugin System
- Custom message handlers
- External tool integration
- Workflow automation

### 4. Multi-Region Support
- Geo-distributed agents
- Regional Redis clusters
- Edge computing compatibility

## Performance Characteristics

### Latency
- Message delivery: <10ms (local)
- Query response: <100ms (typical)
- File lock: <5ms
- Registration: <20ms

### Throughput
- Messages: 1000+ msg/sec
- Concurrent agents: 100+
- File operations: 500+ ops/sec

### Resource Usage
- MCP Server: ~100MB RAM
- Redis: ~1GB for 100 agents
- Network: ~1MB/s per active agent

## Conclusion

A2AMCP's architecture prioritizes simplicity, reliability, and developer experience. By leveraging proven technologies (MCP, Redis, Docker) and focusing on the specific needs of AI agent coordination, it provides a solid foundation for multi-agent development workflows.

The architecture is designed to evolve with the ecosystem, supporting future enhancements while maintaining backward compatibility and operational simplicity.
