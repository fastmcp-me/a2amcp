"""
A2AMCP Python SDK

High-level abstractions for Agent-to-Agent communication via Model Context Protocol.
"""

__version__ = "0.1.4"

from .core import (
    # Core client
    A2AMCPClient,
    Project,
    Agent,
    
    # Managers
    AgentManager,
    InterfaceManager,
    TodoManager,
    AgentTodoManager,
    FileCoordinator,
    AgentCommunication,
    ProjectMonitor,
    
    # Data classes
    AgentInfo,
    Todo,
    FileConflict,
    Interface,
    
    # Enums
    TodoStatus,
    MessageType,
    ConflictStrategy,
    
    # Exceptions
    A2AMCPError,
    ConnectionError,
    ConflictError,
    TimeoutError,
)

from .prompt import (
    PromptBuilder,
    TaskConfig,
    AgentSpawner,
)

__all__ = [
    # Version
    "__version__",
    
    # Core classes
    "A2AMCPClient",
    "Project", 
    "Agent",
    
    # Managers
    "AgentManager",
    "InterfaceManager",
    "TodoManager",
    "AgentTodoManager",
    "FileCoordinator",
    "AgentCommunication",
    "ProjectMonitor",
    
    # Data classes
    "AgentInfo",
    "Todo",
    "FileConflict",
    "Interface",
    
    # Enums
    "TodoStatus",
    "MessageType",
    "ConflictStrategy",
    
    # Exceptions
    "A2AMCPError",
    "ConnectionError",
    "ConflictError",
    "TimeoutError",
    
    # Prompt building
    "PromptBuilder",
    "TaskConfig",
    "AgentSpawner",
]