# Chat Context Toolkit

The **Chat Context Toolkit** is a Python library designed to efficiently manage context for LLM-powered conversations. It provides sophisticated token budget management, long-term archival capabilities, and a virtual file system for exposing files to LLM models, making it ideal for managing chat-based workflows where context preservation and resource optimization are critical.

## Key Features

### History Management

- **Token Budget Management**: Intelligently manage message histories within configurable token limits through message abbreviation and truncation
- **High-Priority Message Preservation**: Protect recent and important messages (like tool calls and their results) from being abbreviated
- **Tool Call Pairing**: Automatically pair assistant tool calls with their corresponding tool result messages to maintain conversation coherence

### Archiving

- **Automatic Chunked Archival**: Archive messages in configurable chunks when token thresholds are exceeded, with background processing
- **Manifest Generation**: Create detailed manifests for each archive chunk including summaries, message IDs, and timestamps
- **State Persistence**: Track archival progress with persistent state management across sessions
- **Archive Retrieval**: Efficiently browse and retrieve archived content with filtering and search capabilities
- **Summarization Integration**: Generate LLM-readable summaries of archived chunks for context understanding

### Virtual File System

- **Unified File Access**: Present files from multiple sources in a single virtual file system for LLM interaction
- **Chat Completion Integration**: Provide built-in tools (`ls`, `view`) for LLMs to explore and read files
- **Multiple File Sources**: Mount different file sources (local filesystem, cloud storage, databases) at various paths
- **Write Tool Support**: Allow file sources to provide custom write tools for file modification

### Protocol-Based Design

- **Pluggable Architecture**: Use protocol-based interfaces for storage providers, token counters, and summarizers
- **Storage Agnostic**: Work with any storage backend by implementing the `StorageProvider` protocol
- **Customizable Token Counting**: Integrate with any tokenization system through the `TokenCounter` protocol
- **Flexible Message Sources**: Support various message sources through `MessageProvider` and `HistoryMessageProvider` protocols

---

## Project Structure

### `archive` Module

Handles the archival of message histories into summarized chunks for long-term storage:

- **`_archive.py`**: Core archiving logic with `ArchiveTask` for periodic archiving and `ArchiveReader` for retrieving archived content.
- **`_state.py`**: Manages the archive's persistent state using configurable storage providers.
- **`_types.py`**: Defines archival data structures, protocols, and configurations including `ArchiveContent`, `ArchiveManifest`, `ArchivesState`, and provider protocols.
- **`ideas.md`**: Development notes and future feature ideas.

### `history` Module

Manages in-memory history for active sessions and ensures prioritization within token budgets:

- **`_history.py`**: Core functionality with `apply_budget_to_history_messages` for token-constrained message processing.
- **`_prioritize.py`**: Logic for pairing and prioritizing messages (e.g., tool calls and results).
- **`_budget.py`**: Ensures that token usage remains within the defined budget through abbreviation and truncation.
- **`_decorators.py`**: Utility decorators for performance logging and timing.
- **`_types.py`**: Type definitions specific to history management including protocols and data structures.

### `virtual_filesystem` Module

Provides a virtual file system abstraction for LLM interaction with files from multiple sources:

- **`virtual_filesystem.py`**: Core `VirtualFileSystem` class that manages file source mounts and provides tools for LLM interaction.
- **`types.py`**: Type definitions including `FileSource`, `DirectoryEntry`, `FileEntry`, and `WriteToolDefinition` protocols.
- **`README.md`**: Detailed documentation on the virtual file system concept and implementation.

---

## Installation

### Requirements

- **Python**: 3.11 or higher

### Setup

To use this library, install the necessary dependencies with the **`uv`** dependency manager:

```bash
uv sync --frozen
```

For development with all dependency groups (including examples):

```bash
uv sync --all-extras --all-groups --frozen
```

---

## Usage

### Example 1: Managing Message History with Token Budgets

```python
from chat_context_toolkit.history import (
    apply_budget_to_history_messages,
    NewTurn,
    HistoryMessageProvider,
    TokenCounter
)

# Create a token counter function
def token_counter(messages):
    # Implement your token counting logic
    return sum(len(msg.get("content", "")) for msg in messages)

# Create a message provider function
async def message_provider(after_id=None):
    # Implement your message retrieval logic
    # Return a sequence of HistoryMessageProtocol objects
    return your_messages

# Apply token budget to message history
turn = NewTurn(high_priority_token_count=5000)
messages = await apply_budget_to_history_messages(
    turn=turn,
    token_budget=10000,
    token_counter=token_counter,
    message_provider=message_provider,
)
```

### Example 2: Archiving Messages

```python
from chat_context_toolkit.archive import ArchiveTask, ArchiveTaskConfig

# Initialize archiving task
archive_task = ArchiveTask(
    storage_provider=your_storage_provider,  # Must implement StorageProvider protocol
    message_provider=your_message_provider,  # Must implement MessageProvider protocol
    token_counter=your_token_counter,        # Must implement TokenCounter protocol
    summarizer=your_summarizer,              # Must implement Summarizer protocol
)

# Start archiving with custom configuration
config = ArchiveTaskConfig(
    message_poll_interval_seconds=300,  # Poll every 5 minutes
    chunk_token_count_threshold=50000   # Archive when chunk exceeds 50k tokens
)
task, trigger_fn = archive_task.start(config=config)

# Optionally trigger archiving manually
trigger_fn()
```

### Example 3: Reading Archived Messages

```python
from chat_context_toolkit.archive import ArchiveReader

# Create archive reader
reader = ArchiveReader(
    message_provider=your_message_provider,
    storage_provider=your_storage_provider,
)

# Get archive state
state = await reader.get_state()
print(f"Most recent archived message: {state.most_recent_archived_message_id}")

# List all archived chunks
async for manifest in reader.list():
    print(f"Archive: {manifest.summary}")
    print(f"Messages: {len(manifest.message_ids)}")
    print(f"Date range: {manifest.timestamp_oldest} to {manifest.timestamp_most_recent}")

# Read specific archive content
content = await reader.read("archive_filename.json")
if content:
    print(f"Found {len(content.messages)} messages in archive")
```

### Example 4: Virtual File System

```python
from chat_context_toolkit.virtual_filesystem import VirtualFileSystem
from openai import OpenAI

# Create and configure virtual file system
vfs = VirtualFileSystem()
vfs.mount("/docs", your_file_source)  # Must implement FileSource protocol

# Get tools for OpenAI chat completion
tools = list(vfs.tools.values())

# Use with OpenAI chat completion
client = OpenAI()
messages = [
    {"role": "system", "content": "You have access to files through the virtual file system. Use the ls and view tools to explore and read files."},
    {"role": "user", "content": "What files are available in /docs?"}
]

response = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools
)

# Execute tool calls from the response
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        result = await vfs.execute_tool(tool_call)
        print(f"Tool {tool_call.function.name} result: {result}")
```

---

## Development Setup

1. Install the project dependencies:

   ```bash
   make install
   ```

2. Run tests:
   ```bash
   make test
   ```
