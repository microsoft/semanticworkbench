import asyncio
from typing import Tuple

async def run_command(cmd: list) -> Tuple[str, str, int]:
    """
    Run an external command asynchronously and return a tuple:
    (stdout, stderr, returncode)
    """
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    ret = process.returncode
    if ret is None:
        ret = -1
    return stdout.decode(), stderr.decode(), int(ret)

async def code_checker(context: str, file_path: str, mode: str = "all") -> dict:
    """
    Run linting (using ruff) and type-checking (using mypy) on the given file.

    Parameters:
      - context: Provided context (not used here).
      - file_path: The path to the code file to check.
      - mode: "all" (default), "lint", or "type-check" to specify which checks to run.

    Returns:
      A dictionary with a success flag and aggregated issues.
    """
    results = {"issues": []}

    # Process linting using ruff
    if mode in ["all", "lint"]:
        cmd_ruff = ["ruff", "check", file_path]
        stdout_ruff, stderr_ruff, code_ruff = await run_command(cmd_ruff)
        print(f"Ruff stdout: {stdout_ruff}")
        print(f"Ruff stderr: {stderr_ruff}")
        if code_ruff != 0:
            # Use stderr if available, else stdout
            lint_output = stderr_ruff if stderr_ruff.strip() else stdout_ruff
        else:
            lint_output = stdout_ruff
        lint_lines = lint_output.strip().splitlines() if lint_output.strip() else []
        for line in lint_lines:
            results["issues"].append({
                "type": "lint",
                "tool": "ruff",
                "message": line
            })

    # Process type-checking using mypy
    if mode in ["all", "type-check"]:
        cmd_mypy = ["mypy", file_path]
        stdout_mypy, stderr_mypy, code_mypy = await run_command(cmd_mypy)
        print(f"Mypy stdout: {stdout_mypy}")
        print(f"Mypy stderr: {stderr_mypy}")
        if code_mypy != 0:
            type_output = stderr_mypy if stderr_mypy.strip() else stdout_mypy
        else:
            type_output = stdout_mypy
        type_lines = type_output.strip().splitlines() if type_output.strip() else []
        for line in type_lines:
            results["issues"].append({
                "type": "type-check",
                "tool": "mypy",
                "message": line
            })

    return {"success": True, "results": results}
