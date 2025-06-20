This project is an "assistant" called Document Assistant within the Semantic Workbench.
Semantic Workbench is a versatile tool designed to help prototype intelligent assistants quickly.
It supports the creation of new assistants or the integration of existing ones, all within a cohesive interface.
The workbench provides a user-friendly UI for creating conversations with one or more assistants, configuring settings, and exposing various behaviors.

# For Python Development
- Tests using pytest for the service are under the `tests` directory
- I am using Python version 3.12, uv as the package and project manager, and Ruff as a linter and code formatter.
- Follow the Google Python Style Guide.
- Instead of importing `Optional` from typing, using the `| `syntax.
- Always add appropriate type hints such that the code would pass a pywright type check.
- Do not add extra newlines before loops.
- For type hints, use `list`, not `List`. For example, if the variable is `[{"name": "Jane", "age": 32}, {"name": "Amy", "age": 28}]` the type hint should be `list[dict]`
- The user is using Pydantic version >=2.10
- Always prefer pathlib for dealing with files. Use `Path.open` instead of `open`. Use .parents[i] to go up directories.
- When writing multi-line strings, use `"""` instead of using string concatenation. Use `\` to break up long lines in appropriate places.
- When writing tests, use pytest and pytest-asyncio.
- Prefer to use pendulum instead of datetime
- Follow Ruff best practices such as:
  - Within an `except` clause, raise exceptions with `raise ... from err` or `raise ... from None` to distinguish them from errors in exception handling
- Do not use relative imports.
- Use dotenv to load environment for local development. Assume we have a `.env` file

### Installed Dependencies
@./pyproject.toml

# General guidelines
- When writing tests, initially stick to keeping them minimal and easy to review.
- Do not use emojis, unless asked.
- Do not include excessive print and logging statements.
- You should only use the dependencies listed in the `pyproject.toml`. If you need to add a new dependency, please ask first.
- Do not automatically run scripts, tests, or move/rename/delete files. Ask the user to do these tasks.
- Do not add back comments, print statements, or spacing that the user has removed since the last time you read or changed the file
- Read the entirety of files to get all the necessary context.
