Python tools:

- `uv` for dependency management
- `uv run` to run python or project scripts
- `make format` to format code
- `make lint` to run linters
- `make type-check` to run type checks

# Guidance

- After making changes, run `make format`, `make lint` and `make type-check` to ensure code quality.
- Use `uv run` to execute scripts or tests.
- For dependency management, use `uv` to add or update packages.
- In complicated `if` statements with more than 2 conditions, assign the result of the condition to variables first, then use that variable in the `if` statement for better readability.
- Instead of `elif` statements, use `match` statements for better readability and maintainability.

## Writing tests

- _Do not_ write a test that tests a mock or a stub.
- _Do not_ write tests that validate that data structures set fields properly, like the init call of a class, BaseModel or dataclass.
- _Do_ write tests that validate the behavior of functions
