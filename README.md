# A2AMCP - Agent-to-Agent Model Context Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-Powered-red.svg)](https://redis.io/)

## Enabling Seamless Multi-Agent Collaboration for AI-Powered Development

A2AMCP brings Google's Agent-to-Agent (A2A) communication concepts to the Model Context Protocol (MCP) ecosystem, enabling AI agents to communicate, coordinate, and collaborate in real-time while working on parallel development tasks.

Originally created for [SplitMind](https://github.com/webdevtodayjason/splitmind), A2AMCP solves the critical problem of isolated AI agents working on the same codebase without awareness of each other's changes.

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/webdevtodayjason/A2AMCP
cd A2AMCP

# Start the server
docker-compose up -d

# Verify it's running
docker ps | grep a2amcp-server
```

### Configure Your Agents

Add to your Claude Code or MCP-compatible agent configuration:

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

## 🎯 What Problem Does A2AMCP Solve?

When multiple AI agents work on the same codebase:
- **Without A2AMCP**: Agents create conflicting code, duplicate efforts, and cause merge conflicts
- **With A2AMCP**: Agents coordinate, share interfaces, prevent conflicts, and work as a team

## 🏗️ Architecture

```
┌─────────────────┐
│   A2AMCP Server │ ← Persistent Redis-backed MCP server
│   (Port 5000)   │   handling all agent communication
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼
┌────────┐┌────────┐┌────────┐┌────────┐
│Agent 1 ││Agent 2 ││Agent 3 ││Agent N │
│Auth    ││Profile ││API     ││Frontend│
└────────┘└────────┘└────────┘└────────┘
```

## 🔧 Core Features

### 1. **Real-time Agent Communication**
- Direct queries between agents
- Broadcast messaging
- Async message queues

### 2. **File Conflict Prevention**
- Automatic file locking
- Conflict detection
- Negotiation strategies

### 3. **Shared Context Management**
- Interface/type registry
- API contract sharing
- Dependency tracking

### 4. **Task Transparency**
- Todo list management
- Progress visibility
- Completion tracking

### 5. **Multi-Project Support**
- Isolated project namespaces
- Redis-backed persistence
- Automatic cleanup

## 📦 Installation Options

### Docker Compose (Production)
```yaml
version: '3.8'
services:
  a2amcp-server:
    image: a2amcp/server:latest
    ports:
      - "5000:5000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
```

### Python SDK
```bash
pip install a2amcp-sdk
```

### JavaScript/TypeScript SDK (Coming Soon)
```bash
npm install @a2amcp/sdk
```

## 🚦 Usage Example

### Python SDK
```python
from a2amcp import A2AMCPClient, Project, Agent

async def run_agent():
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    async with Agent(project, "001", "feature/auth", "Build authentication") as agent:
        # Agent automatically registers and maintains heartbeat
        
        # Coordinate file access
        async with agent.files.coordinate("src/models/user.ts") as file:
            # File is locked, safe to modify
            pass
        # File automatically released
        
        # Share interfaces
        await project.interfaces.register(
            agent.session_name,
            "User",
            "interface User { id: string; email: string; }"
        )
```

### Direct MCP Tool Usage
```python
# Register agent
register_agent("my-project", "task-001", "001", "feature/auth", "Building authentication")

# Query another agent
query_agent("my-project", "task-001", "task-002", "interface", "What's the User schema?")

# Share interface
register_interface("my-project", "task-001", "User", "interface User {...}")
```

## 📚 Documentation

- [Full API Reference](https://github.com/webdevtodayjason/A2AMCP/blob/main/docs/API_REFERENCE.md)
- [Python SDK Documentation](https://github.com/webdevtodayjason/A2AMCP/blob/main/sdk/python/README.md)
- [Architecture Overview](https://github.com/webdevtodayjason/A2AMCP/blob/main/docs/ARCHITECTURE.md)
- [SplitMind Integration Guide](https://github.com/webdevtodayjason/A2AMCP/blob/main/docs/SPLITMIND_INTEGRATION.md)

## 🛠️ SDKs and Tools

### Available Now
- **Python SDK**: Full-featured SDK with async support
- **Docker Deployment**: Production-ready containers

### In Development
- **JavaScript/TypeScript SDK**: For Node.js and browser
- **CLI Tools**: Command-line interface for monitoring
- **Go SDK**: High-performance orchestration
- **Testing Framework**: Mock servers and test utilities

See [SDK Development Progress](https://github.com/webdevtodayjason/A2AMCP/blob/main/sdk/TODO.md) for details.

## 🤝 Integration with AI Frameworks

A2AMCP is designed to work with:
- [SplitMind](https://github.com/webdevtodayjason/splitmind) - Original use case
- Claude Code (via MCP)
- Any MCP-compatible AI agent
- Future: LangChain, CrewAI, AutoGen

## 🔍 How It Differs from A2A

While inspired by Google's A2A protocol, A2AMCP makes specific design choices for AI code development:

| Feature | Google A2A | A2AMCP |
|---------|------------|---------|
| Protocol | HTTP-based | MCP tools |
| State | Stateless | Redis persistence |
| Focus | Generic tasks | Code development |
| Deployment | Per-agent servers | Single shared server |

## 🚀 Roadmap

- [x] Core MCP server with Redis
- [x] Python SDK
- [x] Docker deployment
- [ ] JavaScript/TypeScript SDK
- [ ] CLI monitoring tools
- [ ] SplitMind native integration
- [ ] Framework adapters (LangChain, CrewAI)
- [ ] Enterprise features

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](https://github.com/webdevtodayjason/A2AMCP/blob/main/CONTRIBUTING.md) for guidelines.

### Development Setup
```bash
# Clone repository
git clone https://github.com/webdevtodayjason/A2AMCP
cd A2AMCP

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Start development server
docker-compose -f docker-compose.dev.yml up
```

## 📊 Performance

- Handles 100+ concurrent agents
- Sub-second message delivery
- Automatic cleanup of dead agents
- Horizontal scaling ready

## 🔒 Security

- Project isolation
- Optional authentication (coming soon)
- Encrypted communication (roadmap)
- Audit logging

## 📄 License

MIT License - see [LICENSE](https://github.com/webdevtodayjason/A2AMCP/blob/main/LICENSE) file.

## 🙏 Acknowledgments

- Inspired by [Google's A2A Protocol](https://github.com/google/A2A)
- Built for [SplitMind](https://github.com/webdevtodayjason/splitmind)
- Powered by [Model Context Protocol](https://modelcontextprotocol.io)

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/webdevtodayjason/A2AMCP/issues)
- **Discussions**: [GitHub Discussions](https://github.com/webdevtodayjason/A2AMCP/discussions)
- **Discord**: Coming soon

---

*A2AMCP - Turning isolated AI agents into coordinated development teams*