# For Python Development
- The user is using Python version >=3.11 on Windows 11, uv as the package and project manager, and Ruff as a linter and code formatter
- Follow the Google Python Style Guide
- Always add appropriate type hints such that the code would pass a pyright type check
- Instead of importing `Optional` from typing, using the `| `syntax.
- For type hints, use `list`, not `List`. For example, if the variable is `[{"name": "Jane", "age": 32}, {"name": "Amy", "age": 28}]` the type hint should be `list[dict]`
- Always prefer pathlib for dealing with files. Use `Path.open` instead of `open`
- Prefer to use the following Python packages where appropriate over other the standard library or other options:
  - Pydantic >= 2.10, pendulum instead of datetime, loguru instead of logging