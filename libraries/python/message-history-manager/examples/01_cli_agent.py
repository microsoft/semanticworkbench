"""
Work in Progress!
A minimal example of an agent using Message History Management
"""

import argparse
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv
from liquid import render
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.openai import OpenAIProvider

load_dotenv(override=True)

# File extensions that cannot be viewed
UNSUPPORTED_EXTENSIONS = {".docx", ".pptx", ".xlsx", ".pdf", ".zip", ".rar", ".7z", ".exe", ".dll", ".so"}

# Maximum file size
MAX_FILE_SIZE = 150000

SYSTEM_PROMPT = """You are a helpful assistant with access to file management tools.
You can list files in directories, view the contents of text files, and create new files under {{base_directory}}.
Keep responses concise and friendly."""

# region Helper Functions


def get_api_key(provider: str) -> str:
    """Get API key for the specified provider."""
    env_var = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(f"{env_var} not found in environment variables")
    return api_key


def create_model(provider: str):
    """Create a model based on the provider choice."""
    api_key = get_api_key(provider)

    if provider.lower() == "openai":
        return OpenAIModel("gpt-4.1-mini", provider=OpenAIProvider(api_key=api_key))
    elif provider.lower() == "anthropic":
        return AnthropicModel("claude-sonnet-4-20250514", provider=AnthropicProvider(api_key=api_key))
    else:
        raise ValueError(f"Unsupported provider: {provider}. Choose 'openai' or 'anthropic'")


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


# endregion

# region Initialize Agent


def create_agent(base_directory: str, provider: str) -> Agent:
    """Create an agent with file listing and viewing tools."""
    model = create_model(provider)
    system_prompt = render(SYSTEM_PROMPT, base_directory=base_directory)
    agent = Agent(
        model,
        system_prompt=system_prompt,
    )

    # endregion

    # region Tool Definitions

    @agent.tool_plain
    def list_files(directory_path: str = "") -> str:
        """List files and directories in the specified path.

        Args:
            directory_path: Relative path from the base directory to list.
                          Empty string lists the base directory.
        """
        try:
            if directory_path:
                full_path = Path(base_directory) / directory_path
            else:
                full_path = Path(base_directory)

            # Check if the path is valid
            full_path = full_path.resolve()
            base_path = Path(base_directory).resolve()
            if not str(full_path).startswith(str(base_path)):
                return f"❌ Access denied: Path '{directory_path}' is outside the allowed directory"
            if not full_path.exists():
                return f"❌ Directory '{directory_path}' does not exist"
            if not full_path.is_dir():
                return f"❌ '{directory_path}' is not a directory"

            items = []
            for item in sorted(full_path.iterdir()):
                if item.is_dir():
                    items.append(f"📁 {item.name}/")
                else:
                    size = item.stat().st_size
                    size_str = format_file_size(size)
                    items.append(f"📄 {item.name} ({size_str})")

            if not items:
                return f"📂 Directory '{directory_path or base_directory}' is empty"

            result = f"📂 Contents of '{directory_path or base_directory}':\n"
            result += "\n".join(items)
            return result
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"

    @agent.tool_plain
    def view_file(file_path: str) -> str:
        """View the contents of a text file.

        Args:
            file_path: Relative path from the base directory to the file to view.
        """
        try:
            full_path = Path(base_directory) / file_path
            full_path = full_path.resolve()
            base_path = Path(base_directory).resolve()

            if not str(full_path).startswith(str(base_path)):
                return f"❌ Access denied: Path '{file_path}' is outside the allowed directory"
            if not full_path.exists():
                return f"❌ File '{file_path}' does not exist"
            if not full_path.is_file():
                return f"❌ '{file_path}' is not a file"

            file_extension = full_path.suffix.lower()
            if file_extension in UNSUPPORTED_EXTENSIONS:
                return f"❌ Cannot view files with extension '{file_extension}'. Unsupported file type."

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if len(content) > MAX_FILE_SIZE:
                    return f"📄 File '{file_path}' (truncated to {MAX_FILE_SIZE:,} characters):\n\n{content[:MAX_FILE_SIZE]}... [Content truncated]"
                return f"📄 File '{file_path}':\n\n{content}"
            except UnicodeDecodeError:
                return f"❌ Cannot view '{file_path}': File appears to be binary or uses unsupported encoding"
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"

    @agent.tool_plain
    def create_file(file_path: str, content: str) -> str:
        """Create a new file with the specified content.

        Args:
            file_path: Relative path from the base directory where the new file should be created.
            content: The content to write to the new file.
        """
        try:
            full_path = Path(base_directory) / file_path
            full_path = full_path.resolve()
            base_path = Path(base_directory).resolve()

            if not str(full_path).startswith(str(base_path)):
                return f"❌ Access denied: Path '{file_path}' is outside the allowed directory"
            if full_path.exists():
                return f"❌ File '{file_path}' already exists and you cannot currently overwrite it. Create a new file with a different name."

            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            file_size = len(content)
            size_str = format_file_size(file_size)
            return f"✅ File '{file_path}' created successfully ({size_str})"
        except Exception as e:
            return f"❌ Error creating file: {str(e)}"

    # endregion

    return agent


# region Main CLI Chatbot


async def main(base_directory: str, provider: str):
    print("🤖 Message History Manager CLI Agent")
    print(f"📁 Base directory: {base_directory}")
    print(f"🧠 Using provider: {provider}")
    print("Type 'q' to end the conversation")
    print("=" * 42)

    agent = create_agent(base_directory, provider)
    message_history = []
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break

        if user_input.lower() == "q":
            print("👋 Goodbye!")
            break

        print("🤖 Assistant: ", end="", flush=True)
        async with agent.iter(user_input, message_history=message_history) as agent_run:
            async for node in agent_run:
                if agent.is_call_tools_node(node):
                    for part in node.model_response.parts:
                        if part.part_kind == "text" and part.content.strip():
                            print(f"\n{part.content.strip()}", flush=True)
                        elif part.part_kind == "tool-call":
                            print(f"\n🛠️  Calling tool: {part.tool_name}", flush=True)
                            args_str = str(part.args)
                            if len(args_str) > 100:
                                args_str = args_str[:100] + "..."
                            print(f"   Arguments: {args_str}", flush=True)

        if agent_run.result is not None:
            message_history = agent_run.result.all_messages()
        else:
            print("❌ No result available")


# endregion

# region Entry Point and Args

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--directory",
        "-d",
        type=str,
        default=".",
        help="Base directory for file operations (default: current directory)",
    )
    parser.add_argument(
        "--provider",
        "-p",
        type=str,
        choices=["openai", "anthropic"],
        default="anthropic",
        help="AI provider to use",
    )
    args = parser.parse_args()

    base_dir = Path(args.directory).resolve()
    if not base_dir.exists():
        print(f"❌ Error: Directory '{args.directory}' does not exist")
        exit(1)
    if not base_dir.is_dir():
        print(f"❌ Error: '{args.directory}' is not a directory")
        exit(1)

    asyncio.run(main(str(base_dir), args.provider))

# endregion
