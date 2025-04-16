# Coding Guidelines for Project Assistant

This section outlines the core implementation philosophy and guidelines for all code in this code base. It serves as a central reference for decision-making and development approach throughout the project.

## Core Philosophy

- **Wabi-sabi philosophy**: Embracing simplicity and the essential. Each line serves a clear purpose without unnecessary embellishment.
- **Occam's Razor thinking**: The solution should be as simple as possible, but no simpler.
- **Trust in emergence**: Complex systems work best when built from simple, well-defined components that do one thing well.
- **Present-moment focus**: The code handles what's needed now rather than anticipating every possible future scenario.
- **Pragmatic trust**: The developer trusts external systems enough to interact with them directly, handling failures as they occur rather than assuming they'll happen.

This developer likely values clear documentation, readable code, and believes good architecture emerges from simplicity rather than being imposed through complexity.

## Design Guidelines

### 1. Ruthless Simplicity

- **KISS principle taken to heart**: Keep everything as simple as possible, but no simpler
- **Minimize abstractions**: Every layer of abstraction must justify its existence
- **Start minimal, grow as needed**: Begin with the simplest implementation that meets current needs
- **Avoid future-proofing**: Don't build for hypothetical future requirements
- **Question everything**: Regularly challenge complexity in the codebase

### 2. Architectural Integrity with Minimal Implementation

- **Preserve key architectural patterns**: Follow existing patterns when implementing new features.
- **Simplify implementations**: Maintain pattern benefits with dramatically simpler code.
- **Scrappy but structured**: Lightweight implementations of solid architectural foundations.
- **End-to-end thinking**: Focus on complete flows rather than perfect components.

### 3. Library Usage Philosophy

- **Use libraries as intended**: Minimal wrappers around external libraries.
- **Direct integration**: Avoid unnecessary adapter layers.
- **Selective dependency**: Add dependencies only when they provide substantial value.
- **Understand what you import**: No black-box dependencies.

## Architectural Guidelines

### API Layer

- Implement only essential endpoints.
- Minimal middleware with focused validation.
- Clear error responses with useful messages.
- Consistent patterns across endpoints.

### Database & Storage

- Simple schema focused on current needs.
- Use TEXT/JSON fields to avoid excessive normalization early.
- Add indexes only when needed for performance.
- Delay complex database features until required.

## Coding Guidelines

### Remember

- It's easier to add complexity later than to remove it.
- Code you don't write has no bugs.
- Favor clarity over cleverness.
- The best code is often the simplest.
- Follow existing patterns when implementing new features.

### Code Style

Follow the project's established code style for consistency:

- Use 4 spaces for indentation
- Maximum line length is 120 characters
- Follow PEP 8 naming conventions
- Use type annotations consistently
- Write docstrings for functions and classes

### Quality Checks

You can generally check that code works by running `make lint && make type-check && make test` from the project directory you have made changes in.

#### Linting

Run the linter to check for code quality issues:

```bash
make lint
```

#### Type Checking

To check for type and compilation issues, use the following command:

```bash
make type-check
```

Don't try to "get around" type-check problems. Solve them with proper type handling.

Note: Type checking might report errors related to imports from external dependencies. These are expected in development but should be resolved before deployment.

##### Common Type Issues

- **Parameter name mismatch**: Ensure parameter names match between function declarations and calls
- **Missing imports**: Import necessary types from their source modules.
- **Attribute access**: Only check that attributes exist on dynamicly-typed objects. Use strong typing when possible.
- **Type compatibility**: Ensure assigned values match the expected type (e.g., string vs enum).

#### Testing

Run tests to verify functionality:

```bash
make test
```

For a specific test file:

```bash
uv run python -m pytest tests/test_file.py -v
```

### Important Development Tips that junior devs often get wrong

- Keep the ProjectState enum consistent across all files that use it.
- When modifying model attributes, update all references across the codebase.
- Use Optional typing for parameters that might be None.
- Import Management:
  - Always place imports at the top of the file, organized by stdlib, third-party, and local imports. Keep import statements clean and well-organized to improve code readability
  - - Never use imports inside functions - if a circular dependency exists, use TYPE_CHECKING from the typing module:

    ```python
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from .module import Class  # Import only used for type hints
    ```

- Update tests when changing functionality.
- Do not remove tests unless the functionality they test has also been removed. Never skip tests.
- If you want to run python scripts, you MUST use `uv` from the project directory for them to be in the correct environment.
- You have access to logs in a project's .data/logs directory. They have timestamps in the name, so the latests logs are sorted last.
- Never make any git commits. The QA will do that after they review your code.
