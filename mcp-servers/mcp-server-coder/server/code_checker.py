import asyncio
import json
from typing import Optional


async def run_command(cmd: list) -> str:
    """Run an external command asynchronously and return the stdout as a string."""
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"Command {' '.join(cmd)} failed with error: {stderr.decode().strip()}")
    return stdout.decode()


async def code_checker(context: str, file_path: str, mode: str = "all") -> dict:
    """
    Run linting (using ruff) and type-checking (using mypy) on the given file.

    Parameters:
      - context: Provided context (not used here, but required by MCP tool signature).
      - file_path: The path to the code file to check.
      - mode: "all" (default), "lint", or "type-check" to specify which checks to run.

    Returns:
      A dictionary with a success flag and aggregated issues.
    """
    results = {"issues": []}

    if mode in ["all", "lint"]:
        # Run ruff for linting
        cmd_ruff = ["ruff", "--format", "json", file_path]
        try:
            stdout_ruff = await run_command(cmd_ruff)
            lint_results = json.loads(stdout_ruff) if stdout_ruff.strip() else []
        except Exception as e:
            lint_results = [{"error": str(e)}]
        for issue in lint_results:
            issue["type"] = "lint"
            issue["tool"] = "ruff"
            results["issues"].append(issue)

    if mode in ["all", "type-check"]:
        # Run mypy for type-checking
        cmd_mypy = ["mypy", "--show-json-errors", file_path]
        try:
            stdout_mypy = await run_command(cmd_mypy)
            mypy_output = json.loads(stdout_mypy) if stdout_mypy.strip() else {}
            type_results = mypy_output.get("errors", [])
        except Exception as e:
            type_results = [{"error": str(e)}]
        for issue in type_results:
            issue["type"] = "type-check"
            issue["tool"] = "mypy"
            results["issues"].append(issue)

    return {"success": True, "results": results}
