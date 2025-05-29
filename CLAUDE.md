# Semantic Workbench Developer Guidelines

## AI Context System
**Generate comprehensive codebase context for development:**
* `make ai-context-files` - Generate AI context files for all components
* Files created in `ai_context/generated/` organized by logical boundaries:
  - `PYTHON_LIBRARIES.md` - Core libraries and shared utilities
  - `ASSISTANTS.md` - All assistant implementations and patterns
  - `WORKBENCH_FRONTEND.md` - React app components and UI patterns
  - `WORKBENCH_SERVICE.md` - Backend API, database, and service logic
  - `MCP_SERVERS.md` - Model Context Protocol server implementations
  - `EXAMPLES.md` - Sample code and getting-started templates
  - `TOOLS.md` - Build scripts and development utilities
  - `CONFIGURATION.md` - Root-level configs and project setup

**Using AI Context for Development:**
* **New developers**: Read `CONFIGURATION.md` + `PYTHON_LIBRARIES.md` for project overview
* **Building assistants**: Reference patterns in `ASSISTANTS.md` for consistent implementation
* **Frontend work**: Study component patterns in `WORKBENCH_FRONTEND.md`
* **API development**: Follow service patterns from `WORKBENCH_SERVICE.md`
* **MCP servers**: Use existing servers in `MCP_SERVERS.md` as templates
* **AI tools**: Provide relevant context files for better code generation and debugging
* **Code reviews**: Reference context files to understand cross-component impacts

## Common Commands
* Build/Install: `make install` (recursive for all subdirectories)
* Format: `make format` (runs ruff formatter)
* Lint: `make lint` (runs ruff linter)
* Type-check: `make type-check` (runs pyright)
* Test: `make test` (runs pytest)
* Single test: `uv run pytest tests/test_file.py::test_function -v`
* Frontend: `cd workbench-app && pnpm dev` (starts dev server)
* Workbench service: `cd workbench-service && python -m semantic_workbench_service.start`

## Code Style
### Python
* Indentation: 4 spaces
* Line length: 120 characters
* Imports: stdlib → third-party → local, alphabetized within groups
* Naming: `snake_case` for functions/variables, `CamelCase` for classes, `UPPER_SNAKE_CASE` for constants
* Types: Use type annotations consistently; prefer Union syntax (`str | None`) for Python 3.10+
* Documentation: Triple-quote docstrings with param/return descriptions

### C# (.NET)
* Naming: `PascalCase` for classes/methods/properties, `camelCase` for parameters/local variables, `_camelCase` for private fields
* Error handling: Use try/catch with specific exceptions, `ConfigureAwait(false)` with async
* Documentation: XML comments for public APIs
* Async: Use async/await consistently with cancellation tokens

### TypeScript/React (Frontend)
* Component files: Use PascalCase for component names and files (e.g., `MessageHeader.tsx`)
* Hooks: Prefix with 'use' (e.g., `useConversationEvents.ts`)
* CSS: Use Fluent UI styling with mergeStyle and useClasses pattern
* State management: Redux with Redux Toolkit and RTK Query
* Models: Define strong TypeScript interfaces/types

## Tools
* Python: Uses uv for environment/dependency management
* Linting/Formatting: Ruff (Python), ESLint (TypeScript)
* Type checking: Pyright (Python), TypeScript compiler
* Testing: pytest (Python), React Testing Library (Frontend)
* Frontend: React, Fluent UI v9, Fluent Copilot components
* Package management: uv (Python), pnpm (Frontend)