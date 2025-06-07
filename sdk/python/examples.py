"""
A2AMCP Python SDK - Usage Examples

Shows how to use the SDK for common scenarios.
"""

import asyncio
from typing import List

from a2amcp import (
    A2AMCPClient, 
    Project, 
    Agent,
    PromptBuilder,
    TaskConfig,
    AgentSpawner,
    ConflictStrategy,
    TodoStatus
)


# Example 1: Basic Agent Registration and Communication
async def basic_agent_example():
    """Basic example of agent registration and communication"""
    
    # Initialize client and project
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    # Create an agent
    async with Agent(
        project=project,
        task_id="001",
        branch="feature/auth",
        description="Build authentication system"
    ) as agent:
        
        # Agent is now registered and heartbeat is running
        
        # Add todos
        todo1 = await agent.todos.add("Research JWT libraries", priority=1)
        todo2 = await agent.todos.add("Design User schema", priority=1)
        todo3 = await agent.todos.add("Implement login endpoint", priority=2)
        
        # Start working on first todo
        await agent.todos.start(todo1)
        
        # Check who else is active
        other_agents = await project.agents.list()
        print(f"Working with {len(other_agents) - 1} other agents")
        
        # Work with files
        async with agent.files.coordinate(
            "src/models/user.ts",
            change_type="create",
            description="Creating User model"
        ) as file_path:
            print(f"Working on {file_path}")
            # File is locked here
            # ... create the file ...
            
            # Register the interface
            await project.interfaces.register(
                agent.session_name,
                "User",
                """interface User {
                    id: string;
                    email: string;
                    password: string;
                    role: 'admin' | 'user' | 'guest';
                }""",
                file_path
            )
        # File lock is automatically released
        
        # Mark todo as complete
        await agent.todos.complete(todo1)
        
        # Broadcast completion
        await agent.communication.broadcast(
            "info",
            "User model is ready! Interface 'User' is now available."
        )
        
    # Agent is automatically unregistered here


# Example 2: Agent with Message Handling
async def agent_with_handlers():
    """Example of agent that handles incoming messages"""
    
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    agent = Agent(
        project=project,
        task_id="002",
        branch="feature/api",
        description="Build REST API"
    )
    
    # Define message handlers
    @agent.handles("interface")
    async def handle_interface_query(message):
        """Handle queries about interfaces"""
        if "User" in message['content']:
            return "User interface has: id, email, password, role"
        return "I don't have information about that interface"
    
    @agent.handles("api")
    async def handle_api_query(message):
        """Handle queries about API endpoints"""
        return {
            "endpoints": [
                "POST /api/auth/login",
                "POST /api/auth/register",
                "POST /api/auth/logout"
            ]
        }
    
    @agent.on("todo_completed")
    async def on_todo_completed(event):
        """React to todo completions"""
        print(f"Todo completed: {event['todo']['text']}")
    
    # Register and start processing
    async with agent:
        # Process messages in a loop
        while True:
            await agent.process_messages()
            await asyncio.sleep(5)


# Example 3: Orchestrator Spawning Multiple Agents
async def orchestrator_example():
    """Example of orchestrator spawning multiple agents"""
    
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "ecommerce-v2")
    
    # Define tasks
    tasks = [
        TaskConfig(
            task_id="001",
            branch="feature/authentication",
            description="Build user authentication with JWT",
            prompt="Create a complete authentication system with login, register, and JWT tokens",
            shared_interfaces=["User", "AuthToken"]
        ),
        TaskConfig(
            task_id="002",
            branch="feature/product-catalog",
            description="Create product catalog API",
            prompt="Build product CRUD operations with categories and search",
            depends_on=["001"],  # Depends on auth
            shared_interfaces=["User", "Product"]
        ),
        TaskConfig(
            task_id="003",
            branch="feature/shopping-cart",
            description="Implement shopping cart",
            prompt="Create shopping cart with add/remove items and checkout",
            depends_on=["001", "002"],  # Depends on auth and products
            shared_interfaces=["User", "Product", "Cart"]
        )
    ]
    
    # Spawn agents
    spawner = AgentSpawner(project)
    sessions = await spawner.spawn_multiple(
        tasks,
        worktree_base="/path/to/project/worktrees",
        stagger_delay=3.0  # 3 seconds between starts
    )
    
    print(f"Spawned {len(sessions)} agents: {sessions}")
    
    # Monitor progress
    async with project.monitor() as monitor:
        async for event in monitor.events():
            print(f"Event: {event}")


# Example 4: Conflict Resolution
async def conflict_resolution_example():
    """Example of handling file conflicts"""
    
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    agent = Agent(
        project=project,
        task_id="004",
        branch="feature/refactor",
        description="Refactor user model"
    )
    
    async with agent:
        # Try to lock a file with different strategies
        
        # Strategy 1: Wait for lock (default)
        try:
            await agent.files.lock(
                "src/models/user.ts",
                strategy=ConflictStrategy.WAIT,
                timeout=30
            )
            print("Got lock after waiting")
            await agent.files.release("src/models/user.ts")
        except TimeoutError:
            print("Couldn't get lock within 30 seconds")
        
        # Strategy 2: Abort on conflict
        try:
            await agent.files.lock(
                "src/models/user.ts",
                strategy=ConflictStrategy.ABORT
            )
        except ConflictError as e:
            print(f"File locked by {e.conflict.agent}")
            
        # Strategy 3: Negotiate with other agent
        async def negotiate_lock():
            await agent.files.lock(
                "src/models/user.ts",
                strategy=ConflictStrategy.NEGOTIATE,
                timeout=60
            )
        
        # This will query the locking agent automatically
        await negotiate_lock()


# Example 5: Working with Interfaces
async def interface_example():
    """Example of requiring and using shared interfaces"""
    
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    agent = Agent(
        project=project,
        task_id="005",
        branch="feature/user-profile",
        description="Add user profiles"
    )
    
    async with agent:
        # Wait for required interface
        try:
            user_interface = await project.interfaces.require("User", timeout=60)
            print(f"Got User interface: {user_interface.definition}")
            
            # Create a new interface that extends it
            await project.interfaces.register(
                agent.session_name,
                "UserProfile",
                f"""interface UserProfile extends User {{
                    bio: string;
                    avatar: string;
                    preferences: UserPreferences;
                }}""",
                "src/models/profile.ts"
            )
            
        except TimeoutError:
            # Interface not available, ask who's creating it
            await agent.communication.broadcast(
                "help_needed",
                "I need the User interface to create UserProfile. Who's working on it?"
            )


# Example 6: Advanced Prompt Generation
async def advanced_prompt_example():
    """Example of customizing agent prompts"""
    
    # Create a complex prompt with all features
    prompt = PromptBuilder("ecommerce-v2")\
        .with_task({
            "task_id": "006",
            "branch": "feature/payment",
            "description": "Integrate Stripe payment processing",
            "depends_on": ["cart", "auth"],
            "shared_interfaces": ["User", "Cart", "Order"],
            "required_files": ["src/api/checkout.ts", "src/models/order.ts"]
        })\
        .with_coordination_rules([
            "Check cart implementation before starting",
            "Coordinate with order fulfillment team",
            "Ensure PCI compliance in implementation"
        ])\
        .with_error_recovery()\
        .with_check_interval(20)\
        .with_heartbeat_interval(40)\
        .add_instruction("Use Stripe's latest API version")\
        .add_instruction("Implement webhook handlers for payment events")\
        .add_instruction("Add comprehensive error handling for payment failures")\
        .build()
    
    print("Generated prompt:")
    print(prompt)


# Example 7: Todo-Driven Development
async def todo_driven_example():
    """Example of todo-driven coordination between agents"""
    
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    # Frontend agent waiting for backend
    agent = Agent(
        project=project,
        task_id="007",
        branch="feature/login-ui",
        description="Build login UI"
    )
    
    async with agent:
        # Add todos
        await agent.todos.add("Wait for login API endpoint", priority=1)
        await agent.todos.add("Design login form", priority=1)
        await agent.todos.add("Implement form validation", priority=2)
        await agent.todos.add("Connect to API", priority=1)
        
        # Check backend progress
        all_todos = await project.todos.get_all()
        
        # Find auth agent's todos
        auth_todos = None
        for session, data in all_todos.items():
            if 'auth' in data['description'].lower():
                auth_todos = data['todos']
                break
        
        if auth_todos:
            # Check if login endpoint is ready
            login_ready = any(
                'login endpoint' in todo['text'].lower() 
                and todo['status'] == 'completed'
                for todo in auth_todos
            )
            
            if login_ready:
                print("Login endpoint is ready! Can proceed with UI.")
            else:
                print("Waiting for login endpoint...")
                # Query the auth agent
                auth_agent = await project.agents.find(
                    lambda a: 'auth' in a.description.lower()
                )
                if auth_agent:
                    response = await agent.communication.query(
                        auth_agent.session_name,
                        "timeline",
                        "When will the login endpoint be ready?"
                    )
                    print(f"Auth agent says: {response}")


# Example 8: Project Monitoring Dashboard
async def monitoring_example():
    """Example of monitoring project progress"""
    
    client = A2AMCPClient("localhost:5000")
    project = Project(client, "my-app")
    
    while True:
        # Get project snapshot
        agents = await project.agents.list()
        all_todos = await project.todos.get_all()
        interfaces = await project.interfaces.list()
        recent_changes = await project.get_recent_changes(10)
        
        # Display dashboard
        print("\n" + "="*50)
        print(f"Project: {project.project_id}")
        print(f"Active Agents: {len(agents)}")
        print(f"Shared Interfaces: {len(interfaces)}")
        print("="*50)
        
        # Agent progress
        for session_name, agent_info in agents.items():
            todos = all_todos.get(session_name, {})
            total = todos.get('total_todos', 0)
            completed = todos.get('completed', 0)
            
            progress = (completed / total * 100) if total > 0 else 0
            print(f"\n{session_name} ({agent_info.description})")
            print(f"  Progress: {completed}/{total} ({progress:.0f}%)")
            print(f"  Branch: {agent_info.branch}")
        
        # Recent activity
        print(f"\nRecent Changes:")
        for change in recent_changes[:5]:
            print(f"  - {change['session']} {change['change_type']} {change['file_path']}")
        
        await asyncio.sleep(10)


# Main function to run examples
async def main():
    """Run example based on command line argument"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python examples.py <example_number>")
        print("Examples:")
        print("  1 - Basic agent registration and communication")
        print("  2 - Agent with message handlers")
        print("  3 - Orchestrator spawning multiple agents")
        print("  4 - Conflict resolution strategies")
        print("  5 - Working with shared interfaces")
        print("  6 - Advanced prompt generation")
        print("  7 - Todo-driven development")
        print("  8 - Project monitoring dashboard")
        return
    
    example = int(sys.argv[1])
    
    examples = {
        1: basic_agent_example,
        2: agent_with_handlers,
        3: orchestrator_example,
        4: conflict_resolution_example,
        5: interface_example,
        6: advanced_prompt_example,
        7: todo_driven_example,
        8: monitoring_example
    }
    
    if example in examples:
        await examples[example]()
    else:
        print(f"Unknown example: {example}")


if __name__ == "__main__":
    asyncio.run(main())