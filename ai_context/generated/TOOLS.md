# tools

[collect-files]

**Search:** ['tools']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output']
**Include:** []
**Date:** 5/29/2025, 11:26:49 AM
**Files:** 27

=== File: tools/build_ai_context_files.py ===
#!/usr/bin/env python3
"""
Build AI Context Files Script

This script imports the collect_files module and calls its functions directly
 to generate Markdown files containing code and recipe files for AI context.

This script should be placed at:
[repo_root]/tools/build_ai_context_files.py

And will be run from the repository root.
"""

import argparse
import os
import sys
import datetime
import re
import platform

OUTPUT_DIR = "ai_context/generated"

# We're running from repo root, so that's our current directory
global repo_root
repo_root = os.getcwd()

# Add the tools directory to the Python path
tools_dir = os.path.join(repo_root, "tools")
sys.path.append(tools_dir)

# Import the collect_files module
try:
    import collect_files  # type: ignore
except ImportError:
    print(f"Error: Could not import collect_files module from {tools_dir}")
    print("Make sure this script is run from the repository root.")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build AI Context Files script that collects project files into markdown."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Always overwrite files, even if content unchanged",
    )
    return parser.parse_args()


def ensure_directory_exists(file_path) -> None:
    """Create directory for file if it doesn't exist."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")


def strip_date_line(text: str) -> str:
    """Remove any '**Date:** …' line so we can compare content ignoring timestamps."""
    # Remove the entire line that begins with **Date:**
    return re.sub(r"^\*\*Date:\*\*.*\n?", "", text, flags=re.MULTILINE)


def build_context_files(force=False) -> None:
    # Define the tasks to run for Semantic Workbench
    tasks = [
        # Python Libraries - Core Infrastructure
        {
            "patterns": ["libraries/python/semantic-workbench-api-model", "libraries/python/semantic-workbench-assistant", "libraries/python/events"],
            "output": f"{OUTPUT_DIR}/PYTHON_LIBRARIES_CORE.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["pyproject.toml", "README.md"],
        },
        # Python Libraries - AI Clients
        {
            "patterns": ["libraries/python/anthropic-client", "libraries/python/openai-client", "libraries/python/llm-client"],
            "output": f"{OUTPUT_DIR}/PYTHON_LIBRARIES_AI_CLIENTS.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["pyproject.toml", "README.md"],
        },
        # Python Libraries - Extensions & Tools
        {
            "patterns": ["libraries/python/assistant-extensions", "libraries/python/mcp-extensions", "libraries/python/mcp-tunnel", "libraries/python/content-safety"],
            "output": f"{OUTPUT_DIR}/PYTHON_LIBRARIES_EXTENSIONS.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["pyproject.toml", "README.md"],
        },
        # Python Libraries - Specialized Features
        {
            "patterns": ["libraries/python/assistant-drive", "libraries/python/guided-conversation", "libraries/python/skills"],
            "output": f"{OUTPUT_DIR}/PYTHON_LIBRARIES_SPECIALIZED.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["pyproject.toml", "README.md"],
        },
        # .NET Libraries
        {
            "patterns": ["libraries/dotnet"],
            "output": f"{OUTPUT_DIR}/DOTNET_LIBRARIES.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["*.csproj", "README.md"],
        },
        # Workbench Frontend App
        {
            "patterns": ["workbench-app/src"],
            "output": f"{OUTPUT_DIR}/WORKBENCH_FRONTEND.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png", "*.jpg"],
            "include": ["package.json", "tsconfig.json", "vite.config.ts"],
        },
        # Workbench Backend Service
        {
            "patterns": ["workbench-service"],
            "output": f"{OUTPUT_DIR}/WORKBENCH_SERVICE.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["devdb", "migrations/versions"],
            "include": ["pyproject.toml", "alembic.ini", "migrations/env.py"],
        },
        # Assistants Overview - Common patterns and shared structure
        {
            "patterns": ["assistants/Makefile"],
            "output": f"{OUTPUT_DIR}/ASSISTANTS_OVERVIEW.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["assistants/*/README.md", "assistants/*/pyproject.toml"],
        },
        # Project Assistant - Most complex assistant with project management features
        {
            "patterns": ["assistants/project-assistant"],
            "output": f"{OUTPUT_DIR}/ASSISTANT_PROJECT.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png"],
            "include": ["pyproject.toml", "README.md", "CLAUDE.md"],
        },
        # Document Assistant - Document processing and analysis
        {
            "patterns": ["assistants/document-assistant"],
            "output": f"{OUTPUT_DIR}/ASSISTANT_DOCUMENT.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png", "test_data"],
            "include": ["pyproject.toml", "README.md"],
        },
        # Codespace Assistant - Development environment assistant
        {
            "patterns": ["assistants/codespace-assistant"],
            "output": f"{OUTPUT_DIR}/ASSISTANT_CODESPACE.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png"],
            "include": ["pyproject.toml", "README.md"],
        },
        # Navigator Assistant - Workbench navigation and assistance
        {
            "patterns": ["assistants/navigator-assistant"],
            "output": f"{OUTPUT_DIR}/ASSISTANT_NAVIGATOR.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png"],
            "include": ["pyproject.toml", "README.md"],
        },
        # Prospector Assistant - Advanced agent with artifact creation
        {
            "patterns": ["assistants/prospector-assistant"],
            "output": f"{OUTPUT_DIR}/ASSISTANT_PROSPECTOR.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png", "gc_learnings/images"],
            "include": ["pyproject.toml", "README.md"],
        },
        # Other Assistants - Explorer, Guided Conversation, Skill assistants
        {
            "patterns": ["assistants/explorer-assistant", "assistants/guided-conversation-assistant", "assistants/skill-assistant"],
            "output": f"{OUTPUT_DIR}/ASSISTANTS_OTHER.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png"],
            "include": ["pyproject.toml", "README.md"],
        },
        # MCP Servers
        {
            "patterns": ["mcp-servers"],
            "output": f"{OUTPUT_DIR}/MCP_SERVERS.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["*.svg", "*.png", "data", "test"],
            "include": ["pyproject.toml", "README.md", "package.json"],
        },
        # Examples
        {
            "patterns": ["examples"],
            "output": f"{OUTPUT_DIR}/EXAMPLES.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["pyproject.toml", "*.csproj", "README.md"],
        },
        # Tools and Build Scripts
        {
            "patterns": ["tools"],
            "output": f"{OUTPUT_DIR}/TOOLS.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": [],
        },
        # Configuration and Root Files
        {
            "patterns": ["*.md", "*.toml", "Makefile", "*.json", "*.yml", "*.yaml"],
            "output": f"{OUTPUT_DIR}/CONFIGURATION.md",
            "exclude": collect_files.DEFAULT_EXCLUDE + ["workbench-app", "workbench-service", "assistants", "libraries", "mcp-servers", "examples", "tools"],
            "include": [],
        },
        # Aspire Orchestrator
        {
            "patterns": ["aspire-orchestrator"],
            "output": f"{OUTPUT_DIR}/ASPIRE_ORCHESTRATOR.md",
            "exclude": collect_files.DEFAULT_EXCLUDE,
            "include": ["*.csproj", "*.sln", "appsettings.json"],
        },
    ]

    # Execute each task
    for task in tasks:
        patterns = task["patterns"]
        output = task["output"]
        exclude = task["exclude"]
        include = task["include"]

        # Ensure the output directory exists
        ensure_directory_exists(output)

        print(f"Collecting files for patterns: {patterns}")
        print(f"Excluding patterns: {exclude}")
        print(f"Including patterns: {include}")

        # Collect the files
        files = collect_files.collect_files(patterns, exclude, include)
        print(f"Found {len(files)} files.")

        # Build header
        now = datetime.datetime.now()
        # Use appropriate format specifiers based on the platform
        if platform.system() == "Windows":
            date_str = now.strftime("%#m/%#d/%Y, %#I:%M:%S %p")  # Windows non-padding format
        else:
            date_str = now.strftime("%-m/%-d/%Y, %-I:%M:%S %p")  # Unix non-padding format
        header_lines = [
            f"# {' | '.join(patterns)}",
            "",
            "[collect-files]",
            "",
            f"**Search:** {patterns}",
            f"**Exclude:** {exclude}",
            f"**Include:** {include}",
            f"**Date:** {date_str}",
            f"**Files:** {len(files)}\n\n",
        ]
        header = "\n".join(header_lines)

        # Build content body
        content_body = ""
        for file in files:
            rel_path = os.path.relpath(file)
            content_body += f"=== File: {rel_path} ===\n"
            try:
                with open(file, "r", encoding="utf-8") as f:
                    content_body += f.read()
            except Exception as e:
                content_body += f"[ERROR reading file: {e}]\n"
            content_body += "\n\n"

        new_content = header + content_body

        # If file exists and we're not forcing, compare (ignoring only the date)
        if os.path.exists(output) and not force:
            try:
                with open(output, "r", encoding="utf-8") as f:
                    existing_content = f.read()
                # Strip out date lines from both
                existing_sanitized = strip_date_line(existing_content).strip()
                new_sanitized = strip_date_line(new_content).strip()
                if existing_sanitized == new_sanitized:
                    print(f"No substantive changes in {output}, skipping write.")
                    continue
            except Exception as e:
                print(f"Warning: unable to compare existing file {output}: {e}")

        # Write the file (new or forced update)
        with open(output, "w", encoding="utf-8") as outfile:
            outfile.write(new_content)
        print(f"Written to {output}")


def main():
    args = parse_args()

    # Verify we're in the repository root by checking for key directories/files
    required_paths = [
        os.path.join(repo_root, "tools", "collect_files.py"),
        os.path.join(repo_root, "workbench-service"),
        os.path.join(repo_root, "workbench-app"),
        os.path.join(repo_root, "assistants"),
    ]

    missing_paths = [path for path in required_paths if not os.path.exists(path)]
    if missing_paths:
        print("Warning: This script should be run from the repository root.")
        print("The following expected paths were not found:")
        for path in missing_paths:
            print(f"  - {path}")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)

    build_context_files(force=args.force)


if __name__ == "__main__":
    main()


=== File: tools/build_git_collector_files.py ===
#!/usr/bin/env python3
"""
Runs git-collector → falls back to npx automatically (with --yes) →
shows guidance only if everything fails.
"""

from shutil import which
import subprocess
import sys
import os
from textwrap import dedent

OUTPUT_DIR = "ai_context/git_collector"


# Debug function - can be removed or commented out when fixed
def print_debug_info():
    print("===== DEBUG INFO =====")
    print(f"PATH: {os.environ.get('PATH', '')}")
    npx_location = which("npx")
    print(f"NPX location: {npx_location}")
    print("======================")


def guidance() -> str:
    return dedent(
        """\
        ❌  git-collector could not be run.

        Fixes:
          • Global install ……  npm i -g git-collector
          • Or rely on npx (no install).

        Then re-run:  make ai-context-files
        """
    )


def run(cmd: list[str], capture: bool = True) -> subprocess.CompletedProcess:
    """Run a command, optionally capturing its output."""
    print("→", " ".join(cmd))
    return subprocess.run(
        cmd,
        text=True,
        capture_output=capture,
    )


def main() -> None:
    root = sys.argv[1] if len(sys.argv) > 1 else OUTPUT_DIR

    # Uncomment to see debug info when needed
    # print_debug_info()

    # Preferred runners in order
    runners: list[list[str]] = []
    git_collecto_path = which("git-collector")
    if git_collecto_path:
        runners.append([git_collecto_path])
    pnpm_path = which("pnpm")
    if pnpm_path:
        try:
            # Check if git-collector is available via pnpm by running a simple list command
            # Redirect output to avoid cluttering the console
            result = subprocess.run(
                [pnpm_path, "list", "git-collector"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )

            # If git-collector is in the output, it's installed via pnpm
            if "git-collector" in result.stdout and "ERR" not in result.stdout:
                runners.append([pnpm_path, "exec", "git-collector"])
        except Exception:
            # If any error occurs during check, move to next option
            pass

    # For npx, we need to try multiple approaches
    # First, check if npx is in the PATH
    npx_path = which("npx")
    if npx_path:
        # Use the full path to npx if we can find it
        runners.append([npx_path, "--yes", "git-collector"])
    else:
        # Fallback to just the command name as a last resort
        runners.append(["npx", "--yes", "git-collector"])

    if not runners:
        sys.exit(guidance())

    last_result = None
    for r in runners:
        # Capture output for git-collector / pnpm, but stream for npx (shows progress)
        is_npx = "npx" in r[0].lower() if isinstance(r[0], str) else False
        is_git_collector = "git-collector" in r[0].lower() if isinstance(r[0], str) else False
        capture = not (is_npx or is_git_collector)

        print(f"Executing command: {' '.join(r + [root, '--update'])}")
        try:
            last_result = run(r + [root, "--update"], capture=capture)
        except Exception as e:
            print(f"Error executing command: {e}")
            continue
        if last_result.returncode == 0:
            return  # success 🎉
        if r[:2] == ["pnpm", "exec"]:
            print("pnpm run not supported — falling back to npx …")

    # All attempts failed → print stderr (if any) and guidance
    if last_result and last_result.stderr:
        print(last_result.stderr.strip(), file=sys.stderr)
    sys.exit(guidance())


if __name__ == "__main__":
    main()


=== File: tools/collect_files.py ===
#!/usr/bin/env python3
"""
Collect Files Utility

Recursively scans the specified file/directory patterns and outputs a single Markdown
document containing each file's relative path and its content.

Usage examples:
  # Collect all Python files in the current directory:
  python collect_files.py *.py > my_python_files.md

  # Collect all files in the 'output' directory:
  python collect_files.py output > my_output_dir_files.md

  # Collect specific files, excluding 'utils' and 'logs', but including Markdown files from 'utils':
  python collect_files.py *.py --exclude "utils,logs,__pycache__,*.pyc" --include "utils/*.md" > my_output.md
"""

import argparse
import datetime
import fnmatch
import glob
import os
import pathlib
from typing import List, Optional, Set, Tuple

# Default exclude patterns: common directories and binary files to ignore.
DEFAULT_EXCLUDE = [".venv", "node_modules", "*.lock", ".git", "__pycache__", "*.pyc", "*.ruff_cache", "logs", "output"]


def parse_patterns(pattern_str: str) -> List[str]:
    """Splits a comma-separated string into a list of stripped patterns."""
    return [p.strip() for p in pattern_str.split(",") if p.strip()]


def resolve_pattern(pattern: str) -> str:
    """
    Resolves a pattern that might contain relative path navigation.
    Returns the absolute path of the pattern.
    """
    # Convert the pattern to a Path object
    pattern_path = pathlib.Path(pattern)

    # Check if the pattern is absolute or contains relative navigation
    if os.path.isabs(pattern) or ".." in pattern:
        # Resolve to absolute path
        return str(pattern_path.resolve())

    # For simple patterns without navigation, return as is
    return pattern


def match_pattern(path: str, pattern: str, component_matching=False) -> bool:
    """
    Centralized pattern matching logic.

    Args:
        path: File path to match against
        pattern: Pattern to match
        component_matching: If True, matches individual path components
                           (used primarily for exclude patterns)

    Returns:
        True if path matches the pattern
    """
    # For simple exclude-style component matching
    if component_matching:
        parts = os.path.normpath(path).split(os.sep)
        for part in parts:
            if fnmatch.fnmatch(part, pattern):
                return True
        return False

    # Convert paths to absolute for consistent comparison
    abs_path = os.path.abspath(path)

    # Handle relative path navigation in the pattern
    if ".." in pattern or "/" in pattern or "\\" in pattern:
        # If pattern contains path navigation, resolve it to an absolute path
        resolved_pattern = resolve_pattern(pattern)

        # Check if this is a directory pattern with a wildcard
        if "*" in resolved_pattern:
            # Get the directory part of the pattern
            pattern_dir = os.path.dirname(resolved_pattern)
            # Get the filename pattern
            pattern_file = os.path.basename(resolved_pattern)

            # Check if the file is in or under the pattern directory
            file_dir = os.path.dirname(abs_path)
            if file_dir.startswith(pattern_dir):
                # Match the filename against the pattern
                return fnmatch.fnmatch(os.path.basename(abs_path), pattern_file)
            return False  # Not under the pattern directory
        else:
            # Direct file match
            return abs_path == resolved_pattern or fnmatch.fnmatch(abs_path, resolved_pattern)
    else:
        # Regular pattern without navigation, use relative path matching
        return fnmatch.fnmatch(path, pattern)


def should_exclude(path: str, exclude_patterns: List[str]) -> bool:
    """
    Returns True if any component of the path matches an exclude pattern.
    """
    for pattern in exclude_patterns:
        if match_pattern(path, pattern, component_matching=True):
            return True
    return False


def should_include(path: str, include_patterns: List[str]) -> bool:
    """
    Returns True if the path matches any of the include patterns.
    Handles relative path navigation in include patterns.
    """
    for pattern in include_patterns:
        if match_pattern(path, pattern):
            return True
    return False


def collect_files(patterns: List[str], exclude_patterns: List[str], include_patterns: List[str]) -> List[str]:
    """
    Collects file paths matching the given patterns, applying exclusion first.
    Files that match an include pattern are added back in.

    Returns a sorted list of absolute file paths.
    """
    collected = set()

    # Process included files with simple filenames or relative paths
    for pattern in include_patterns:
        # Check for files in the current directory first
        direct_matches = glob.glob(pattern, recursive=True)
        for match in direct_matches:
            if os.path.isfile(match):
                collected.add(os.path.abspath(match))

        # Then check for relative paths
        if ".." in pattern or os.path.isabs(pattern):
            resolved_pattern = resolve_pattern(pattern)

            # Direct file inclusion
            if "*" not in resolved_pattern and os.path.isfile(resolved_pattern):
                collected.add(resolved_pattern)
            else:
                # Pattern with wildcards
                directory = os.path.dirname(resolved_pattern)
                if os.path.exists(directory):
                    filename_pattern = os.path.basename(resolved_pattern)
                    for root, _, files in os.walk(directory):
                        for file in files:
                            if fnmatch.fnmatch(file, filename_pattern):
                                full_path = os.path.join(root, file)
                                collected.add(os.path.abspath(full_path))

    # Process the main patterns
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        for path in matches:
            if os.path.isfile(path):
                process_file(path, collected, exclude_patterns, include_patterns)
            elif os.path.isdir(path):
                process_directory(path, collected, exclude_patterns, include_patterns)

    return sorted(collected)


def process_file(file_path: str, collected: Set[str], exclude_patterns: List[str], include_patterns: List[str]) -> None:
    """Process a single file"""
    abs_path = os.path.abspath(file_path)
    rel_path = os.path.relpath(file_path)

    # Skip if excluded and not specifically included
    if should_exclude(rel_path, exclude_patterns) and not should_include(rel_path, include_patterns):
        return

    collected.add(abs_path)


def process_directory(
    dir_path: str, collected: Set[str], exclude_patterns: List[str], include_patterns: List[str]
) -> None:
    """Process a directory recursively"""
    for root, dirs, files in os.walk(dir_path):
        # Filter directories based on exclude patterns, but respect include patterns
        dirs[:] = [
            d
            for d in dirs
            if not should_exclude(os.path.join(root, d), exclude_patterns)
            or should_include(os.path.join(root, d), include_patterns)
        ]

        # Process each file in the directory
        for file in files:
            full_path = os.path.join(root, file)
            process_file(full_path, collected, exclude_patterns, include_patterns)


def read_file(file_path: str) -> Tuple[str, Optional[str]]:
    """
    Read a file and return its content.

    Returns:
        Tuple of (content, error_message)
    """
    # Check if file is likely binary
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\0" in chunk:  # Simple binary check
                return "[Binary file not displayed]", None

        # If not binary, read as text
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read(), None
    except UnicodeDecodeError:
        # Handle encoding issues
        return "[File contains non-UTF-8 characters]", None
    except Exception as e:
        return "", f"[ERROR reading file: {e}]"


def format_output(
    file_paths: List[str],
    format_type: str,
    exclude_patterns: List[str],
    include_patterns: List[str],
    patterns: List[str],
) -> str:
    """
    Format the collected files according to the output format.

    Args:
        file_paths: List of absolute file paths to format
        format_type: Output format type ("markdown" or "plain")
        exclude_patterns: List of exclusion patterns (for info)
        include_patterns: List of inclusion patterns (for info)
        patterns: Original input patterns (for info)

    Returns:
        Formatted output string
    """
    output_lines = []

    # Add metadata header
    now = datetime.datetime.now()
    date_str = now.strftime("%-m/%-d/%Y, %-I:%M:%S %p")
    output_lines.append(f"# {patterns}")
    output_lines.append("")
    output_lines.append("[collect-files]")
    output_lines.append("")
    output_lines.append(f"**Search:** {patterns}")
    output_lines.append(f"**Exclude:** {exclude_patterns}")
    output_lines.append(f"**Include:** {include_patterns}")
    output_lines.append(f"**Date:** {date_str}")
    output_lines.append(f"**Files:** {len(file_paths)}\n\n")

    # Process each file
    for file_path in file_paths:
        rel_path = os.path.relpath(file_path)

        # Add file header based on format
        if format_type == "markdown":
            output_lines.append(f"### File: {rel_path}")
            output_lines.append("```")
        else:
            output_lines.append(f"=== File: {rel_path} ===")

        # Read and add file content
        content, error = read_file(file_path)
        if error:
            output_lines.append(error)
        else:
            output_lines.append(content)

        # Add file footer based on format
        if format_type == "markdown":
            output_lines.append("```")

        # Add separator between files
        output_lines.append("\n")

    return "\n".join(output_lines)


def main() -> None:
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Recursively collect files matching the given patterns and output a document with file names and content."
    )
    parser.add_argument("patterns", nargs="+", help="File and/or directory patterns to collect (e.g. *.py or output)")
    parser.add_argument(
        "--exclude",
        type=str,
        default="",
        help="Comma-separated patterns to exclude (will be combined with default excludes: "
        + ",".join(DEFAULT_EXCLUDE)
        + ")",
    )
    parser.add_argument(
        "--include", type=str, default="", help="Comma-separated patterns to include (overrides excludes if matched)"
    )
    parser.add_argument(
        "--format", type=str, choices=["markdown", "plain"], default="plain", help="Output format (default: plain)"
    )
    args = parser.parse_args()

    # Parse pattern arguments and combine with default excludes
    user_exclude_patterns = parse_patterns(args.exclude)
    exclude_patterns = DEFAULT_EXCLUDE + user_exclude_patterns

    include_patterns = parse_patterns(args.include) if args.include else []

    # Collect files
    patterns = args.patterns
    files = collect_files(patterns, exclude_patterns, include_patterns)

    # Format and print output
    output = format_output(files, args.format, exclude_patterns, include_patterns, patterns)
    print(output)


if __name__ == "__main__":
    main()


=== File: tools/docker/Dockerfile.assistant ===
# syntax=docker/dockerfile:1

# Dockerfile for assistants
# Context root is expected to be the root of the repo
ARG python_image=python:3.11-slim

# These build arguments will differ per assistant:
# package is the directory name of the assistant package under /assistants
ARG package
ARG app

FROM ${python_image} AS build

ARG package

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# copy all library packages
COPY ./libraries/python /packages/libraries/python
# copy the assistant package
COPY ./assistants/${package} /packages/assistants/assistant

# install the assistant and dependencies to /.venv
RUN uv sync --directory /packages/assistants/assistant --no-editable --no-dev --locked

FROM ${python_image}

ARG app

# BEGIN: enable ssh in azure web app - comment out if not needed
########
# install sshd and set password for root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && echo "root:Docker!" | chpasswd

# azure sshd config
COPY ./tools/docker/azure_website_sshd.conf /etc/ssh/sshd_config
ENV SSHD_PORT=2222
########
# END: enable ssh in azure web app

# BEGIN: install devtunnels CLI - comment out if not needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl libsecret-1-0 libicu-dev \
    && rm -rf /var/lib/apt/lists/* \
    && curl -sL -o /bin/devtunnel https://tunnelsassetsprod.blob.core.windows.net/cli/linux-x64-devtunnel \
    && chmod +x /bin/devtunnel
ENV DEVTUNNEL_COMMAND_PATH=/bin/devtunnel
# END: install devtunnels CLI


RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /packages/assistants/assistant/.venv /packages/assistants/assistant/.venv
ENV PATH=/packages/assistants/assistant/.venv/bin:$PATH

COPY ./tools/docker/docker-entrypoint.sh /scripts/docker-entrypoint.sh
RUN chmod +x /scripts/docker-entrypoint.sh

ENV ASSISTANT_APP=${app}

ENV assistant__host=0.0.0.0
ENV assistant__port=3001
ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/scripts/docker-entrypoint.sh"]
CMD ["start-assistant"]


=== File: tools/docker/Dockerfile.mcp-server ===
# syntax=docker/dockerfile:1

# Dockerfile for mcp-servers
# Context root is expected to be the root of the repo
ARG python_image=python:3.11-slim

# These build arguments will differ per mcp-server:
# package is the directory name of the mcp-server package under /mcp-servers
ARG package
ARG main_module

FROM ${python_image} AS build

ARG package

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# copy all library packages
COPY ./libraries/python /packages/libraries/python
# copy the assistant package
COPY ./mcp-servers/${package} /packages/mcp-servers/mcp-server

# install the mcp-server and dependencies to /.venv
RUN uv sync --directory /packages/mcp-servers/mcp-server --no-editable --no-dev --locked

FROM ${python_image}

ARG main_module

# BEGIN: enable ssh in azure web app - comment out if not needed
########
# install sshd and set password for root
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && echo "root:Docker!" | chpasswd

# azure sshd config
COPY ./tools/docker/azure_website_sshd.conf /etc/ssh/sshd_config
ENV SSHD_PORT=2222
########
# END: enable ssh in azure web app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gettext \
    && rm -rf /var/lib/apt/lists/*

COPY --from=build /packages/mcp-servers/mcp-server/.venv /packages/mcp-servers/mcp-server/.venv
ENV PATH=/packages/mcp-servers/mcp-server/.venv/bin:$PATH

COPY ./tools/docker/docker-entrypoint.sh /scripts/docker-entrypoint.sh
RUN chmod +x /scripts/docker-entrypoint.sh

ENV MAIN_MODULE=${main_module}
ENV PORT=3001
ENV PYTHONUNBUFFERED=1

SHELL ["/bin/bash", "-c"]
ENTRYPOINT ["/scripts/docker-entrypoint.sh"]
CMD ["python", "-m", "${MAIN_MODULE}", "--transport", "sse", "--port", "${PORT}"]


=== File: tools/docker/azure_website_sshd.conf ===
Port 			        2222
ListenAddress 		    0.0.0.0
LoginGraceTime 		    180
X11Forwarding 		    yes
Ciphers                 aes128-cbc,3des-cbc,aes256-cbc,aes128-ctr,aes192-ctr,aes256-ctr
MACs                    hmac-sha1,hmac-sha1-96
StrictModes 		    yes
SyslogFacility 		    DAEMON
PasswordAuthentication  yes
PermitEmptyPasswords 	no
PermitRootLogin 	    yes
Subsystem               sftp internal-sftp


=== File: tools/docker/docker-entrypoint.sh ===
#!/bin/bash

set -e

# if SSHD_PORT is set, start sshd
if [ -n "${SSHD_PORT}" ]; then
    service ssh start
fi

cmd=$(echo "$@" | envsubst)
exec ${cmd}


=== File: tools/makefiles/docker-assistant.mk ===
repo_root = $(shell git rev-parse --show-toplevel)
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# the directory containing the assistant's Makefile is expected to be
# the directory of the assistant
invoking_makefile_directory = $(notdir $(patsubst %/,%,$(dir $(realpath $(firstword $(MAKEFILE_LIST))))))

ASSISTANT_APP ?= assistant:app
ASSISTANT_PACKAGE ?= $(invoking_makefile_directory)
ASSISTANT_IMAGE_NAME ?= $(subst -,_,$(invoking_makefile_directory))

DOCKER_PATH = $(repo_root)
DOCKER_FILE = $(repo_root)/tools/docker/Dockerfile.assistant
DOCKER_BUILD_ARGS = app=$(ASSISTANT_APP) package=$(ASSISTANT_PACKAGE)
DOCKER_IMAGE_NAME = $(ASSISTANT_IMAGE_NAME)

AZURE_WEBSITE_NAME ?= $(ASSISTANT_PACKAGE)-service

include $(mkfile_dir)/docker.mk


ASSISTANT__WORKBENCH_SERVICE_URL ?= http://host.docker.internal:3000

docker-run-local: docker-build
	docker run --rm -it --add-host=host.docker.internal:host-gateway --env assistant__workbench_service_url=$(ASSISTANT__WORKBENCH_SERVICE_URL) $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)


.PHONY: start
start:
	uv run start-assistant


=== File: tools/makefiles/docker-mcp-server.mk ===
repo_root = $(shell git rev-parse --show-toplevel)
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# the directory containing the mcp-servers's Makefile is expected to be
# the directory of the mcp-server
invoking_makefile_directory = $(notdir $(patsubst %/,%,$(dir $(realpath $(firstword $(MAKEFILE_LIST))))))

MCP_SERVER_PACKAGE ?= $(invoking_makefile_directory)
MCP_SERVER_IMAGE_NAME ?= $(subst -,_,$(invoking_makefile_directory))
MCP_SERVER_MAIN_MODULE ?= $(MCP_SERVER_IMAGE_NAME).start

DOCKER_PATH = $(repo_root)
DOCKER_FILE = $(repo_root)/tools/docker/Dockerfile.mcp-server
DOCKER_BUILD_ARGS = main_module=$(MCP_SERVER_MAIN_MODULE) package=$(MCP_SERVER_PACKAGE)
DOCKER_IMAGE_NAME = $(MCP_SERVER_IMAGE_NAME)

AZURE_WEBSITE_NAME ?= $(MCP_SERVER_PACKAGE)-service

include $(mkfile_dir)/docker.mk

docker-run-local: docker-build
	docker run --rm -it --add-host=host.docker.internal:host-gateway $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)


=== File: tools/makefiles/docker.mk ===
DOCKER_REGISTRY_NAME ?=
ifneq ($(DOCKER_REGISTRY_NAME),)
DOCKER_REGISTRY_HOST ?= $(DOCKER_REGISTRY_NAME).azurecr.io
endif
DOCKER_IMAGE_TAG ?= $(shell git rev-parse HEAD)
DOCKER_PUSH_LATEST ?= true
DOCKER_PATH ?= .
DOCKER_FILE ?= Dockerfile
DOCKER_BUILD_ARGS ?=

AZURE_WEBSITE_NAME ?=
AZURE_WEBSITE_SLOT ?= staging
AZURE_WEBSITE_TARGET_SLOT ?= production
AZURE_WEBSITE_SUBSCRIPTION ?=
AZURE_WEBSITE_RESOURCE_GROUP ?=

require_value = $(foreach var,$(1),$(if $(strip $($(var))),,$(error "Variable $(var) is not set: $($(var))")))

.PHONY: .docker-build
.docker-build:
	$(call require_value,DOCKER_IMAGE_NAME DOCKER_IMAGE_TAG DOCKER_FILE DOCKER_PATH)
ifdef DOCKER_BUILD_ARGS
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(foreach arg,$(DOCKER_BUILD_ARGS),--build-arg $(arg)) $(DOCKER_PATH) -f $(DOCKER_FILE)
else
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(DOCKER_PATH) -f $(DOCKER_FILE)
endif

.PHONY: .docker-push
.docker-push: .docker-build
	$(call require_value,DOCKER_REGISTRY_NAME DOCKER_REGISTRY_HOST DOCKER_IMAGE_NAME DOCKER_IMAGE_TAG)
	az acr login --name $(DOCKER_REGISTRY_NAME)
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
	docker push $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
ifeq ($(DOCKER_PUSH_LATEST),true)
	docker tag $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME)
	docker push $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME)
endif

define update-container
	az webapp config container set \
		--subscription $(AZURE_WEBSITE_SUBSCRIPTION) \
		--resource-group $(AZURE_WEBSITE_RESOURCE_GROUP) \
		--name $(1) --slot $(AZURE_WEBSITE_SLOT) \
		--container-image-name $(DOCKER_REGISTRY_HOST)/$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

endef

define swap-slots
	az webapp deployment slot swap \
		--subscription $(AZURE_WEBSITE_SUBSCRIPTION) \
		--resource-group $(AZURE_WEBSITE_RESOURCE_GROUP) \
		--name $(1) \
		--slot $(AZURE_WEBSITE_SLOT) \
		--target-slot $(AZURE_WEBSITE_TARGET_SLOT) \
		--verbose

endef

.PHONY: .azure-container-deploy
.azure-container-deploy:
	$(call require_value,AZURE_WEBSITE_SUBSCRIPTION AZURE_WEBSITE_NAME AZURE_WEBSITE_SLOT AZURE_WEBSITE_RESOURCE_GROUP DOCKER_REGISTRY_HOST DOCKER_IMAGE_NAME DOCKER_IMAGE_TAG)
	$(foreach website_name,$(AZURE_WEBSITE_NAME),$(call update-container,$(website_name)))
ifneq ($(AZURE_WEBSITE_SLOT),$(AZURE_WEBSITE_TARGET_SLOT))
	$(foreach website_name,$(AZURE_WEBSITE_NAME),$(call swap-slots,$(website_name)))
endif

ifndef DISABLE_DEFAULT_DOCKER_TARGETS
docker-build: .docker-build
docker-push: .docker-push
docker-deploy: .azure-container-deploy
endif


=== File: tools/makefiles/python.mk ===
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(mkfile_dir)/shell.mk

.DEFAULT_GOAL ?= install

ifdef UV_PROJECT_DIR
uv_project_args = --directory $(UV_PROJECT_DIR)
venv_dir = $(UV_PROJECT_DIR)/.venv
else
venv_dir = .venv
endif

UV_SYNC_INSTALL_ARGS ?= --all-extras --frozen
UV_RUN_ARGS ?= --all-extras --frozen

PYTEST_ARGS ?= --color=yes

## Rules

.PHONY: install
install:
	uv sync $(uv_project_args) $(UV_SYNC_INSTALL_ARGS)

.PHONY: lock-upgrade
lock-upgrade:
	uv lock --upgrade $(uv_project_args)

.PHONY: lock
lock:
	uv sync $(uv_project_args) $(UV_SYNC_LOCK_ARGS)

.PHONY: clean
clean:
	$(rm_dir) $(venv_dir) $(ignore_failure)

.PHONY: lint
lint:
	uvx ruff check --no-cache --fix .

.PHONY: format
format:
	uvx ruff format --no-cache .

ifneq ($(findstring pytest,$(if $(shell $(call command_exists,uv) $(stderr_redirect_null)),$(shell uv tree --depth 1 $(stderr_redirect_null)),)),)
PYTEST_EXISTS=true
endif
ifneq ($(findstring pyright,$(if $(shell $(call command_exists,uv) $(stderr_redirect_null)),$(shell uv tree --depth 1 $(stderr_redirect_null)),)),)
PYRIGHT_EXISTS=true
endif

ifeq ($(PYRIGHT_EXISTS),true)
.PHONY: type-check test
test: type-check
type-check:
	uv run $(uv_project_args) $(UV_RUN_ARGS) pyright $(PYRIGHT_ARGS)
endif

ifeq ($(PYTEST_EXISTS),true)
.PHONY: test pytest
test: pytest
pytest:
	uv run $(uv_project_args) $(UV_RUN_ARGS) pytest $(PYTEST_ARGS)
endif


=== File: tools/makefiles/recursive.mk ===
# Runs make in all recursive subdirectories with a Makefile, passing the make target to each.
# Directories are make'ed in top down order.
# ex: make (runs DEFAULT_GOAL)
# ex: make clean (runs clean)
# ex: make install (runs install)
mkfile_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))

# if IS_RECURSIVE_MAKE is set, then this is being invoked by another recursive.mk.
# in that case, we don't want any targets
ifndef IS_RECURSIVE_MAKE

.DEFAULT_GOAL := install

# make with VERBOSE=1 to print all outputs of recursive makes
VERBOSE ?= 0

RECURSIVE_TARGETS = clean install test format lint type-check lock ai-context-files

# You can pass in a list of files or directories to retain when running `clean/git-clean`
# ex: make clean GIT_CLEAN_RETAIN=".env .data"
# As always with make, you can also set this as an environment variable
GIT_CLEAN_RETAIN ?= .env
GIT_CLEAN_EXTRA_ARGS = $(foreach v,$(GIT_CLEAN_RETAIN),--exclude !$(v))
ifeq ($(VERBOSE),0)
GIT_CLEAN_EXTRA_ARGS += --quiet
endif


.PHONY: git-clean
git-clean:
	git clean -dffX . $(GIT_CLEAN_EXTRA_ARGS)

FILTER_OUT = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
MAKE_FILES = $(shell find . -mindepth 2 -name Makefile)
ALL_MAKE_DIRS = $(sort $(filter-out ./,$(dir $(MAKE_FILES))))
ifeq ($(suffix $(SHELL)),.exe)
MAKE_FILES = $(shell dir Makefile /b /s)
ALL_MAKE_DIRS = $(sort $(filter-out $(subst /,\,$(abspath ./)),$(patsubst %\,%,$(dir $(MAKE_FILES)))))
endif

MAKE_DIRS := $(call FILTER_OUT,site-packages,$(call FILTER_OUT,node_modules,$(ALL_MAKE_DIRS)))

.PHONY: .clean-error-log .print-error-log

MAKE_CMD_MESSAGE = $(if $(MAKECMDGOALS), $(MAKECMDGOALS),)

.clean-error-log:
	@$(rm_file) $(call fix_path,$(mkfile_dir)/make*.log) $(ignore_output) $(ignore_failure)

.print-error-log:
ifeq ($(suffix $(SHELL)),.exe)
	@if exist $(call fix_path,$(mkfile_dir)/make_error_dirs.log) ( \
		echo Directories failed to make$(MAKE_CMD_MESSAGE): && \
		type $(call fix_path,$(mkfile_dir)/make_error_dirs.log) && \
		($(rm_file) $(call fix_path,$(mkfile_dir)/make*.log) $(ignore_output) $(ignore_failure)) && \
		exit 1 \
	)
else
	@if [ -e $(call fix_path,$(mkfile_dir)/make_error_dirs.log) ]; then \
		echo "\n\033[31;1mDirectories failed to make$(MAKE_CMD_MESSAGE):\033[0m\n"; \
		cat $(call fix_path,$(mkfile_dir)/make_error_dirs.log); \
		echo ""; \
		$(rm_file) $(call fix_path,$(mkfile_dir)/make*.log) $(ignore_output) $(ignore_failure); \
		exit 1; \
	fi
endif

.PHONY: $(RECURSIVE_TARGETS) $(MAKE_DIRS)

clean: git-clean

# Special target that only runs at root level (not recursive)
.PHONY: ai-context-files
ai-context-files:
	@echo "Building AI context files..."
	@python tools/build_ai_context_files.py
	@python tools/build_git_collector_files.py 2>/dev/null || echo "Note: git-collector not available, skipping external docs"
	@echo "AI context files generated in ai_context/generated/"

# Exclude ai-context-files from recursive processing
$(filter-out ai-context-files,$(RECURSIVE_TARGETS)): .clean-error-log $(MAKE_DIRS) .print-error-log

$(MAKE_DIRS):
ifdef FAIL_ON_ERROR
	$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1
else
	@$(rm_file) $(call fix_path,$@/make*.log) $(ignore_output) $(ignore_failure)
	@echo make -C $@ $(MAKECMDGOALS)
ifeq ($(suffix $(SHELL)),.exe)
	@$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1 1>$(call fix_path,$@/make.log) $(stderr_redirect_stdout) || \
		( \
			(findstr /c:"*** No" $(call fix_path,$@/make.log) ${ignore_output}) || ( \
				echo $@ >> $(call fix_path,$(mkfile_dir)/make_error_dirs.log) && \
				$(call touch,$@/make_error.log) \
			) \
		)
	@if exist $(call fix_path,$@/make_error.log) echo make -C $@$(MAKE_CMD_MESSAGE) failed:
	@if exist $(call fix_path,$@/make_error.log) $(call touch,$@/make_print.log)
	@if "$(VERBOSE)" neq "0" $(call touch,$@/make_print.log)
	@if exist $(call fix_path,$@/make_print.log) type $(call fix_path,$@/make.log)
else
	@$(MAKE) -C $@ $(MAKECMDGOALS) IS_RECURSIVE_MAKE=1 1>$(call fix_path,$@/make.log) $(stderr_redirect_stdout) || \
		( \
			grep -qF "*** No" $(call fix_path,$@/make.log) || ( \
				echo "\t$@" >> $(call fix_path,$(mkfile_dir)/make_error_dirs.log) ; \
				$(call touch,$@/make_error.log) ; \
			) \
		)
	@if [ -e $(call fix_path,$@/make_error.log) ]; then \
		echo "\n\033[31;1mmake -C $@$(MAKE_CMD_MESSAGE) failed:\033[0m\n" ; \
	fi
	@if [ "$(VERBOSE)" != "0" -o -e $(call fix_path,$@/make_error.log) ]; then \
		cat $(call fix_path,$@/make.log); \
	fi
endif
	@$(rm_file) $(call fix_path,$@/make*.log) $(ignore_output) $(ignore_failure)
endif # ifdef FAIL_ON_ERROR

endif # ifndef IS_RECURSIVE_MAKE

include $(mkfile_dir)/shell.mk


=== File: tools/makefiles/shell.mk ===
# posix shell
rm_dir = rm -rf
rm_file = rm -rf
fix_path = $(1)
touch = touch $(1)
true_expression = true
stdout_redirect_null = 1>/dev/null
stderr_redirect_null = 2>/dev/null
stderr_redirect_stdout = 2>&1
command_exists = command -v $(1)

# windows shell
ifeq ($(suffix $(SHELL)),.exe)
rm_dir = rd /s /q
rm_file = del /f /q
fix_path = $(subst /,\,$(abspath $(1)))
# https://ss64.com/nt/touch.html
touch = type nul >> $(call fix_path,$(1)) && copy /y /b $(call fix_path,$(1))+,, $(call fix_path,$(1)) $(ignore_output)
true_expression = VER>NUL
stdout_redirect_null = 1>NUL
stderr_redirect_null = 2>NUL
stderr_redirect_stdout = 2>&1
command_exists = where $(1)
endif

ignore_output = $(stdout_redirect_null) $(stderr_redirect_stdout)
ignore_failure = || $(true_expression)


=== File: tools/reset-service-data.ps1 ===
#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root

# ================================================================

# Remove the specified files
Remove-Item -Force "workbench-service/.data/workbench.db"

=== File: tools/reset-service-data.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

rm -f workbench-service/.data/workbench.db


=== File: tools/run-app.ps1 ===
#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root

# ================================================================

# Change directory to workbench-app
Set-Location "workbench-app"

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
$nodeVersion = & node -v
if ($nodeVersion -notmatch "^v20\..*") {
  Write-Host "Node version must be 20.x.x. You have $nodeVersion. Please install the correct version. See also README.md for instructions."
  Write-Host "If you use 'nvm' you can also run 'nvm install 20'"
  exit 1
}

Write-Host "Starting the Semantic Workbench app, open https://localhost:4000 in your browser when ready"

pnpm install
pnpm start

=== File: tools/run-app.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd workbench-app

# Check node version, it must be major version 20 (any minor), otherwise show an error and exit
NODE_VERSION=$(node -v)
if [[ ! $NODE_VERSION =~ ^v(1[8-9]|[2-9][0-9]).* ]]; then
    echo "Node version is $NODE_VERSION, expected 18.x.x or higher."

  # Attempt to source nvm
  if [ -s "$NVM_DIR/nvm.sh" ]; then
    . "$NVM_DIR/nvm.sh"
  elif [ -s "$HOME/.nvm/nvm.sh" ]; then
    export NVM_DIR="$HOME/.nvm"
    . "$NVM_DIR/nvm.sh"
  else
    echo "nvm not found. Please install Node 18 or higher manually."
    echo "See also README.md for instructions."
    exit 1
  fi

  echo "Installing latest LTS Node version via nvm..."
  nvm install --lts
  nvm use --lts

  NODE_VERSION=$(node -v)
  if [[ ! $NODE_VERSION =~ ^v(1[8-9]|[2-9][0-9]).* ]]; then
    echo "Failed to switch to Node 18 or higher via nvm. You have $NODE_VERSION."
    exit 1
  fi
fi

echo "Starting the Semantic Workbench app, open https://localhost:4000 in your browser when ready"

pnpm install
pnpm start


=== File: tools/run-canonical-agent.ps1 ===
#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root
# ================================================================

# Change directory to workbench-service
Set-Location "workbench-service"

# Run the command
uv run start-assistant semantic_workbench_assistant.canonical:app


=== File: tools/run-canonical-agent.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd workbench-service

uv run start-assistant semantic_workbench_assistant.canonical:app


=== File: tools/run-dotnet-examples-with-aspire.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd aspire-orchestrator

echo '===================================================================='
echo ''
echo 'If the Aspire dashboard is not opened in your browser automatically '
echo 'look in the log for the following link, including the auth token:   '
echo ''
echo '            https://localhost:17149/login?t=........                '
echo ''
echo '===================================================================='

. run.sh


=== File: tools/run-python-example1.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd examples/python/python-01-echo-bot

uv run start-assistant


=== File: tools/run-python-example2.ps1 ===
#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root
# ================================================================

# Change directory to examples/python/python-02-simple-chatbot
Set-Location "examples/python/python-02-simple-chatbot"

# Run the commands
uv run start-assistant


=== File: tools/run-python-example2.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd examples/python/python-02-simple-chatbot

uv run start-assistant


=== File: tools/run-service.ps1 ===
#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root
# ================================================================

# Change directory to workbench-service
Set-Location "workbench-service"

# Note: this creates the .data folder at
# path         ./workbench-service/.data
# rather than  ./workbench-service/.data
uv run start-service


=== File: tools/run-service.sh ===
#!/usr/bin/env bash

set -e
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && cd .. && pwd)"
cd $ROOT
# ================================================================

cd workbench-service

# Note: this creates the .data folder at
# path         ./workbench-service/.data
# rather than  ./workbench-service/.data
uv run start-service


=== File: tools/run-workbench-chatbot.ps1 ===
#!/usr/bin/env pwsh

# Exit on error
$ErrorActionPreference = "Stop"

# Determine the root directory of the script
$scriptPath = $PSScriptRoot
$root = Resolve-Path "$scriptPath\.."

# Change directory to the root
Set-Location $root

# Run the scripts
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-File", "$root\tools\run-service.ps1" -PassThru
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-File", "$root\tools\run-python-example2.ps1" -PassThru
Start-Process -FilePath "pwsh" -ArgumentList "-NoExit", "-File", "$root\tools\run-app.ps1" -PassThru


=== File: tools/run-workbench-chatbot.sh ===
#!/usr/bin/env bash

# Exit on error
set -e

# Determine the root directory of the script
scriptPath=$(dirname "$(realpath "$0")")
root=$(realpath "$scriptPath/..")

# Change directory to the root
cd "$root"

# Run the scripts in separate tmux sessions
tmux new-session -d -s service "bash $root/tools/run-service.sh"
tmux new-session -d -s python_example "bash $root/tools/run-python-example2.sh"
tmux new-session -d -s app "bash $root/tools/run-app.sh"

# Attach to the tmux session
tmux attach-session -t app

# Detach from the current session (inside tmux)
# Ctrl+b d

# Switch to a different session (inside tmux)
# Ctrl+b s

# tmux list-sessions
# tmux attach-session -t <session-name>
# tmux kill-session -t <session-name>

