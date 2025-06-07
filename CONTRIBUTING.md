# Contributing to A2AMCP

First off, thank you for considering contributing to A2AMCP! It's people like you that make A2AMCP such a great tool for the AI development community.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Configure A2AMCP with '...'
2. Run agent with '....'
3. Execute command '....'
4. See error

**Expected behavior**
What you expected to happen.

**Environment:**
 - OS: [e.g. Ubuntu 22.04]
 - Python version: [e.g. 3.11]
 - A2AMCP version: [e.g. 0.1.0]
 - Docker version: [if applicable]

**Additional context**
Add any other context, logs, or screenshots.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use case**: Explain why this enhancement would be useful
- **Proposed solution**: Describe your ideal solution
- **Alternatives**: List any alternative solutions you've considered
- **Additional context**: Add any other context or screenshots

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the existing style
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.8+ 
- Docker and Docker Compose
- Redis (via Docker)
- Git

### Local Development

1. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/A2AMCP.git
   cd A2AMCP
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Start Redis**
   ```bash
   docker-compose up -d redis
   ```

5. **Run the MCP server locally**
   ```bash
   python mcp_server_redis.py
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=a2amcp

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest -v
```

### Code Style

We use the following tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking

Run all checks:
```bash
# Format code
black .
isort .

# Check linting
flake8

# Check types
mypy .
```

## Project Structure

```
A2AMCP/
├── mcp_server_redis.py    # Core MCP server implementation
├── docker-compose.yml     # Docker configuration
├── docs/                  # Documentation
│   ├── API_REFERENCE.md   # API documentation
│   └── ARCHITECTURE.md    # Architecture overview
├── sdk/                   # SDKs for different languages
│   ├── python/           # Python SDK
│   ├── javascript/       # JavaScript/TypeScript SDK (planned)
│   └── TODO.md          # SDK development tracking
├── tests/                # Test suite
└── examples/            # Usage examples
```

## SDK Development

### Adding a New SDK

1. Create a new directory under `sdk/` for your language
2. Follow the API patterns established by the Python SDK
3. Include:
   - Core client implementation
   - Type definitions/interfaces
   - Lifecycle management
   - Examples
   - Tests
   - README with quickstart
4. Update the main README.md
5. Add to sdk/TODO.md

### SDK Design Principles

- **Simple by default**: Easy things should be easy
- **Powerful when needed**: Complex things should be possible
- **Type safe**: Use language features for type safety
- **Consistent API**: Similar patterns across SDKs
- **Well documented**: Every public API needs docs
- **Tested**: Aim for >80% test coverage

## Documentation

### Writing Documentation

- Use clear, simple language
- Include code examples for every feature
- Explain the "why" not just the "how"
- Keep examples realistic and practical
- Update docs with any API changes

### Documentation Structure

- **README.md**: Quick start and overview
- **API_REFERENCE.md**: Complete API documentation
- **SDK READMEs**: Language-specific guides
- **Examples**: Working code examples

## Testing Guidelines

### Writing Tests

- Write tests for new features
- Include both unit and integration tests
- Test error conditions and edge cases
- Use descriptive test names
- Mock external dependencies

### Test Structure

```python
def test_agent_registration():
    """Test that agent can register with server"""
    # Arrange
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "test-project")
    
    # Act
    agent = Agent(project, "001", "feature/test", "Test")
    result = await agent.register()
    
    # Assert
    assert result['status'] == 'registered'
    assert agent._registered is True
```

## Release Process

1. Update version numbers:
   - `sdk/python/setup.py`
   - `sdk/python/src/a2amcp/__init__.py`
   - Main README.md

2. Update CHANGELOG.md

3. Create release PR

4. After merge, tag release:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

5. Build and publish packages

## Community

### Getting Help

- **Discord**: Join our community (coming soon)
- **GitHub Discussions**: Ask questions and share ideas
- **Stack Overflow**: Tag questions with `a2amcp`

### Roadmap Discussions

Major features are discussed in GitHub Discussions before implementation:
- Architectural changes
- New SDK languages
- Breaking API changes
- Integration strategies

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project README

## Quick Contribution Checklist

- [ ] Fork the repository
- [ ] Create a feature branch (`git checkout -b feature/amazing-feature`)
- [ ] Make your changes
- [ ] Add/update tests
- [ ] Update documentation
- [ ] Run tests and linting
- [ ] Commit with clear message
- [ ] Push to your fork
- [ ] Open a Pull Request
- [ ] Wait for review

## Questions?

Feel free to:
- Open an issue for clarification
- Ask in GitHub Discussions
- Reach out to maintainers

Thank you for contributing to A2AMCP! 🎉