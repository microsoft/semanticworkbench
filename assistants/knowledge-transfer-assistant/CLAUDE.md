# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Knowledge Transfer Assistant

A dual-mode context transfer system that facilitates collaborative knowledge sharing between Coordinators and Team members in the Semantic Workbench. This assistant bridges information gaps through structured communication with shared artifacts, real-time updates, and bidirectional information flow.

## Architecture Overview

### Dual Mode Operation

The assistant operates in two distinct conversation roles determined by metadata:

1. **Coordinator Mode**: Knowledge organizers create and manage knowledge bases, provide guidance, and respond to information requests
2. **Team Mode**: Team members access shared knowledge, explore project context, and request additional information

**Role Detection**: Uses `detect_assistant_role()` to check conversation metadata `project_role` field. Capabilities are role-specific through tool registration.

### Conversation Structure

The system manages three types of conversations:

- **Coordinator Conversation**: Personal workspace for knowledge organizers
- **Shareable Team Conversation**: Template conversation with share URL (never directly used)
- **Team Conversation(s)**: Individual conversations for team members accessing shared knowledge

### Key Components

- `assistant/assistant.py`: Main assistant implementation with dual-role event handling
- `assistant/manager.py`: Project state and artifact management (KnowledgeTransferManager)
- `assistant/conversation_share_link.py`: Cross-conversation linking and synchronization
- `assistant/inspectors/`: Modular inspector panel system (brief, learning, sharing, debug)
- `assistant/notifications.py`: Cross-conversation notification and UI refresh system
- `assistant/storage.py` & `assistant/storage_models.py`: Persistent state management
- `assistant/config.py`: Role-specific prompt templates and configuration
- `assistant/data.py`: Core data models and enums (including InspectorTab)

## Common Commands

- Build/Install: `make install`
- Format: `make format` (runs ruff formatter)
- Lint: `make lint` (runs ruff linter)
- Type-check: `make type-check` (runs pyright)
- Test: `make test` (runs pytest)
- Single test: `uv run pytest tests/test_file.py::test_function -v`
- Manual inspector test: `python tests/test_inspector.py` (test state inspector functionality)
- Docker build: `make docker-build` (builds assistant container image)
- Start assistant: `make start` (starts the assistant service)
- Local docker run: `make docker-run-local` (runs assistant in Docker with local workbench)

## Development Notes

### Inspector Panel UI Refresh System

The assistant uses a sophisticated event-driven system to keep inspector panels synchronized across all conversations:

- **InspectorTab Enum**: Defines available inspector panels with their state IDs (`data.py`)
- **refresh_current_ui()**: Updates inspector panels in the current conversation only
- **refresh_all_project_uis()**: Updates inspector panels across all conversations in a project
- **ProjectNotifier.notify_project_update()**: Sends notifications and refreshes UIs with optional tab targeting
- **State Events**: Uses `AssistantStateEvent` with specific state IDs to trigger UI updates

**Key Pattern**: When updating project state, always call the appropriate refresh function with specific tabs:
```python
from .data import InspectorTab
await ShareStorage.refresh_all_share_uis(context, share_id, [InspectorTab.BRIEF])
```

### State Management

- **Cross-Conversation Linking**: Connects coordinator and team conversations through project IDs
- **File Synchronization**: Automatic file sharing between linked conversations
- **Artifact Storage**: Structured data models for project briefs, knowledge digests, and information requests
- **Inspector Panel System**: Multi-panel real-time dashboard with specific state IDs:
  - `brief`: Knowledge brief and project overview
  - `objectives`: Learning objectives and outcomes
  - `requests`: Information requests and sharing status
  - `debug`: Debug information and project state
- **UI Refresh Architecture**: Event-driven system using `AssistantStateEvent` with specific state IDs
- **Auto-Update Knowledge Digest**: LLM-powered automatic extraction and updating of key information from conversations

### Auto-Update Knowledge Digest

The system automatically extracts and updates key information from conversations:

- **Trigger**: Every Coordinator message automatically triggers `auto_update_knowledge_digest()`
- **Process**: Analyzes chat history using LLM to extract important information
- **Storage**: Updates the knowledge digest with extracted content marked as auto-generated
- **UI Refresh**: Ensures debug panel refreshes after completion (both success and error cases)
- **Pattern**: Always refreshes UI regardless of success/failure to maintain consistency

### Configuration Templates

The assistant supports two templates with unified codebase:

- **Default Template**: Full project management with goals, criteria, and progress tracking
- **Context Transfer Template**: Simplified knowledge sharing without formal project stages

### Key Artifacts

- **Project Brief**: Knowledge goals and success criteria
- **Knowledge Digest**: Dynamically updated context repository (auto-generated from conversations)
- **Learning Objectives**: Structured goals with specific learning outcomes
- **Information Requests**: Bidirectional communication between coordinators and team members
- **Inspector Panels**: Real-time multi-panel dashboard showing project state


### Dependencies

The assistant uses several key dependencies from the Semantic Workbench ecosystem:

- `semantic-workbench-assistant`: Core assistant framework
- `assistant-extensions[attachments]`: File attachment support with dashboard cards and navigation
- `content-safety`: Content moderation capabilities
- `openai-client`: LLM integration for knowledge digest generation
- `openai>=1.61.0`: Direct OpenAI API integration

### Project Structure

Key architectural files:
- `/assistant/`: Core implementation files
  - `assistant.py`: Main assistant with dual-role event handling
  - `manager.py`: Project state and artifact management (KnowledgeTransferManager)
  - `conversation_share_link.py`: Cross-conversation linking and synchronization
  - `notifications.py`: Cross-conversation notification and UI refresh system
  - `data.py`: Core data models and enums (InspectorTab, RequestPriority, etc.)
  - `inspectors/`: Modular inspector panel system
    - `brief.py`: Brief inspector for knowledge transfer status
    - `learning.py`: Learning objectives inspector
    - `sharing.py`: Sharing status inspector
    - `debug.py`: Debug inspector
    - `common.py`: Common inspector utilities
  - `storage.py` & `storage_models.py`: Persistent state management
  - `config.py`: Role-specific prompt templates and configuration
  - `text_includes/`: Role-specific prompts and instruction templates
  - `assets/`: SVG icons and visual assets
- `/docs/`: Design documentation including `DESIGN.md`, `DEV_GUIDE.md`, `JTBD.md`, and `WORKBENCH_NOTES.md`
- `/tests/`: Comprehensive test suite with manual inspector testing support

## Code Style

### Python

- Indentation: 4 spaces
- Line length: 120 characters
- Imports: stdlib → third-party → local, alphabetized within groups
- Naming: `snake_case` for functions/variables, `CamelCase` for classes, `UPPER_SNAKE_CASE` for constants
- Types: Use type annotations consistently; prefer Union syntax (`str | None`) for Python 3.10+
- Documentation: Triple-quote docstrings with param/return descriptions

## Tools

- Python: Uses uv for environment/dependency management
- Linting/Formatting: Ruff (Python)
- Type checking: Pyright (Python)
- Testing: pytest (Python)
- Package management: uv (Python)

## Testing

The assistant includes comprehensive test coverage:
- `test_artifact_loading.py`: Artifact loading and management tests
- `test_inspector.py`: State inspector functionality tests (can be run manually with `python tests/test_inspector.py`)
- `test_share_manager.py`: File sharing and synchronization tests
- `test_share_storage.py`: Storage system tests
- `test_share_tools.py`: Tool functionality tests
- `test_team_mode.py`: Team mode operation tests

## Philosophy

The codebase follows a **wabi-sabi philosophy** emphasizing:
- Ruthless simplicity with minimal abstractions
- Present-moment focus rather than future-proofing
- Trust in emergence from simple, well-defined components
- Direct library integration with minimal wrappers
- Pragmatic trust in external systems
