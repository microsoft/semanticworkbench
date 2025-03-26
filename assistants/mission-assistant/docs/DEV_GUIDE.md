# Coding Guidelines for Mission Assistant

## Cortex Platform Implementation Philosophy

This section outlines the core implementation philosophy and guidelines for the Cortex Platform. It serves as a central reference for decision-making and development approach throughout the project.

### Core Philosophy

Embodies a Zen-like minimalism that values simplicity and clarity above all. This approach reflects:

- **Wabi-sabi philosophy**: Embracing simplicity and the essential. Each line serves a clear purpose without unnecessary embellishment.
- **Occam's Razor thinking**: The solution should be as simple as possible, but no simpler.
- **Trust in emergence**: Complex systems work best when built from simple, well-defined components that do one thing well.
- **Present-moment focus**: The code handles what's needed now rather than anticipating every possible future scenario.
- **Pragmatic trust**: The developer trusts external systems enough to interact with them directly, handling failures as they occur rather than assuming they'll happen.

This developer likely values clear documentation, readable code, and believes good architecture emerges from simplicity rather than being imposed through complexity.

### Core Design Principles

#### 1. Ruthless Simplicity

- **KISS principle taken to heart**: Keep everything as simple as possible, but no simpler
- **Minimize abstractions**: Every layer of abstraction must justify its existence
- **Start minimal, grow as needed**: Begin with the simplest implementation that meets current needs
- **Avoid future-proofing**: Don't build for hypothetical future requirements
- **Question everything**: Regularly challenge complexity in the codebase

#### 2. Architectural Integrity with Minimal Implementation

- **Preserve key architectural patterns**: MCP for service communication, SSE for events, separate I/O channels
- **Simplify implementations**: Maintain pattern benefits with dramatically simpler code
- **Scrappy but structured**: Lightweight implementations of solid architectural foundations
- **End-to-end thinking**: Focus on complete flows rather than perfect components

#### 3. Library Usage Philosophy

- **Use libraries as intended**: Minimal wrappers around external libraries
- **Direct integration**: Avoid unnecessary adapter layers
- **Selective dependency**: Add dependencies only when they provide substantial value
- **Understand what you import**: No black-box dependencies

### Technical Implementation Guidelines

#### API Layer

- Implement only essential endpoints
- Minimal middleware with focused validation
- Clear error responses with useful messages
- Consistent patterns across endpoints

#### Database & Storage

- Simple schema focused on current needs
- Use TEXT/JSON fields to avoid excessive normalization early
- Add indexes only when needed for performance
- Delay complex database features until required

#### MCP Implementation

- Streamlined MCP clients focused on core functionality
- Direct error handling without excessive layering
- Simple, functional approach to service interactions

#### SSE Implementation

```python
# Simple, focused SSE connection manager
class ConnectionManager:
    def __init__(self):
        self.connections = {}
        
    async def add_connection(self, resource_id, user_id):
        """Add a new SSE connection"""
        connection_id = str(uuid.uuid4())
        queue = asyncio.Queue()
        self.connections[connection_id] = {
            "resource_id": resource_id,
            "user_id": user_id,
            "queue": queue
        }
        return queue, connection_id

    async def send_event(self, resource_id, event_type, data):
        """Send an event to all connections for a resource"""
        # Direct delivery to relevant connections only
        for conn_id, conn in self.connections.items():
            if conn["resource_id"] == resource_id:
                await conn["queue"].put({
                    "event": event_type,
                    "data": data
                })
```

#### Good Example: Simple MCP Client

```python
# Focused MCP client with clean error handling
class McpClient:
    def __init__(self, endpoint: str, service_name: str):
        self.endpoint = endpoint
        self.service_name = service_name
        self.client = None

    async def connect(self):
        """Connect to MCP server"""
        if self.client is not None:
            return  # Already connected

        try:
            # Create SSE client context
            async with sse_client(self.endpoint) as (read_stream, write_stream):
                # Create client session
                self.client = ClientSession(read_stream, write_stream)
                # Initialize the client
                await self.client.initialize()
        except Exception as e:
            self.client = None
            raise RuntimeError(f"Failed to connect to {self.service_name}: {str(e)}")

    async def call_tool(self, name: str, arguments: dict):
        """Call a tool on the MCP server"""
        if not self.client:
            await self.connect()

        return await self.client.call_tool(name=name, arguments=arguments)
```

### Remember

- It's easier to add complexity later than to remove it
- Code you don't write has no bugs
- Favor clarity over cleverness
- The best code is often the simplest

## Development Workflow

### Code Style
Follow the project's established code style for consistency:
- Use 4 spaces for indentation
- Maximum line length is 120 characters
- Follow PEP 8 naming conventions
- Use type annotations consistently
- Write docstrings for functions and classes

### Quality Checks

#### Linting
Run the linter to check for code quality issues:
```bash
make lint
```

#### Type Checking 
To check for type issues, use the following command:
```bash
make type-check
```

Note: Type checking might report errors related to imports from external dependencies. These are expected in development but should be resolved before deployment.

#### Testing
Run tests to verify functionality:
```bash
make test
```

For a specific test file:
```bash
python -m pytest tests/test_file.py -v
```

### Common Type Issues
- **Parameter name mismatch**: Ensure parameter names match between function declarations and calls
- **Missing imports**: Import necessary types from their source modules
- **Attribute access**: Check that attributes exist on the objects they're accessed from
- **Type compatibility**: Ensure assigned values match the expected type (e.g., string vs enum)

### Development Tips
1. Keep the MissionState enum consistent across all files that use it
2. When modifying model attributes, update all references across the codebase
3. Use Optional typing for parameters that might be None
4. Follow existing patterns when implementing new features
5. Import Management:
   - Always place imports at the top of the file, organized by stdlib, third-party, and local imports
   - Handle circular dependencies with TYPE_CHECKING from typing module:
   ```python
   from typing import TYPE_CHECKING
   
   if TYPE_CHECKING:
       from .module import Class  # Import only used for type hints
   ```
   - Never use imports inside functions - if a circular dependency exists, use TYPE_CHECKING
   - Keep import statements clean and well-organized to improve code readability
6. Update tests when changing functionality