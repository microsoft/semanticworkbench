# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Knowledge Transfer Assistant

A dual-mode context transfer system that facilitates collaborative knowledge sharing between Coordinators and Team members in the Semantic Workbench. This assistant bridges information gaps through structured communication with shared artifacts, real-time updates, and bidirectional information flow.

## Architecture Overview

### Dual Mode Operation

The assistant operates in two distinct conversation roles:

1. **Coordinator Mode**: Knowledge organizers create and manage knowledge bases, provide guidance, and respond to information requests
2. **Team Mode**: Team members access shared knowledge, explore project context, and request additional information

### Conversation Structure

The system manages three types of conversations:

- **Coordinator Conversation**: Personal workspace for knowledge organizers
- **Shareable Team Conversation**: Template conversation with share URL (never directly used)
- **Team Conversation(s)**: Individual conversations for team members accessing shared knowledge

### Key Components

- `assistant/assistant.py`: Main assistant implementation with dual-role event handling
- `assistant/manager.py`: Project state and artifact management
- `assistant/conversation_share_link.py`: Cross-conversation linking and synchronization
- `assistant/command_processor.py`: Command handling with role-based authorization
- `assistant/state_inspector.py`: Real-time project dashboard
- `assistant/storage.py` & `assistant/storage_models.py`: Persistent state management
- `assistant/config.py`: Role-specific prompt templates and configuration

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

### State Management

- **Cross-Conversation Linking**: Connects coordinator and team conversations through project IDs
- **File Synchronization**: Automatic file sharing between linked conversations
- **Artifact Storage**: Structured data models for project briefs, whiteboards, and information requests
- **Inspector Panel**: Real-time visual dashboard showing project state

### Configuration Templates

The assistant supports two templates with unified codebase:

- **Default Template**: Full project management with goals, criteria, and progress tracking
- **Context Transfer Template**: Simplified knowledge sharing without formal project stages

### Key Artifacts

- **Project Brief**: Knowledge goals and success criteria
- **Project Whiteboard**: Dynamically updated context repository
- **Information Requests**: Bidirectional communication between coordinators and team members
- **Project Dashboard**: Real-time progress and state information

### Available Commands

#### General Commands (All Users)
- `/help [command]` - Get help with available commands
- `/knowledge-info [brief|digest|status|requests]` - View knowledge package information

#### Coordinator Commands
- `/create-knowledge-brief Title|Description` - Create a knowledge brief
- `/add-learning-objective Objective Name|Description|Learning outcome 1;Learning outcome 2` - Add learning objectives
- `/resolve-request request_id|Resolution information` - Resolve information requests
- `/list-participants` - List all project participants

#### Team Commands
- `/request-info Request Title|Description|priority` - Request information from coordinator
- `/update-status status|progress|message` - Update project status and progress
- `/sync-files` - Synchronize shared files from the project

### Dependencies

The assistant uses several key dependencies from the Semantic Workbench ecosystem:

- `semantic-workbench-assistant`: Core assistant framework
- `assistant-extensions[attachments]`: File attachment support with dashboard cards and navigation
- `content-safety`: Content moderation capabilities
- `openai-client`: LLM integration

### Project Structure

Key architectural files:
- `/assistant/`: Core implementation files
  - `assistant.py`: Main assistant with dual-role event handling
  - `manager.py`: Project state and artifact management
  - `conversation_share_link.py`: Cross-conversation linking and synchronization
  - `command_processor.py`: Command handling with role-based authorization
  - `inspectors/`: State inspector components (brief, learning, sharing, debug)
  - `storage.py` & `storage_models.py`: Persistent state management
  - `config.py`: Role-specific prompt templates and configuration
  - `text_includes/`: Role-specific prompts and instruction templates
- `/docs/`: Design documentation including `DESIGN.md`, `DEV_GUIDE.md`, and `WORKBENCH_NOTES.md`
- `/tests/`: Test suite with manual inspector testing support

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
