# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Knowledge Transfer Assistant

A sophisticated dual-mode assistant that facilitates collaborative knowledge sharing between Coordinators (knowledge creators) and Team members (knowledge receivers) within the Semantic Workbench platform.

## Core Architecture

### Dual-Mode Operation
The assistant operates in two distinct modes with role-specific capabilities:

1. **Coordinator Mode**: Creates and manages knowledge packages, responds to information requests, shares files
2. **Team Mode**: Accesses shared knowledge, requests information, tracks learning progress

### Cross-Conversation Communication
The system manages three types of conversations:
- **Coordinator Conversation**: Personal workspace for knowledge creation
- **Shareable Team Conversation**: Template conversation (never directly used)
- **Team Conversation(s)**: Individual conversations for each team member

### Key Components

- **Knowledge Transfer Manager** (`assistant/domain/`): Orchestrates the entire knowledge transfer lifecycle
- **Share Manager** (`assistant/files.py`): Handles file synchronization across conversations
- **Storage System** (`assistant/storage.py`, `assistant/storage_models.py`): Persistent state management
- **UI Tabs** (`assistant/ui-tabs/`): Real-time visual dashboards showing transfer status
- **Notification System** (`assistant/notifications.py`): Cross-conversation communication

### Core Artifacts
- **Knowledge Brief**: Introductory overview for team members
- **Knowledge Digest**: Auto-updating LLM-generated information repository
- **Learning Objectives**: Structured goals with specific outcomes
- **Information Requests**: Team member questions with priority levels

## Development Commands

### Basic Operations
```bash
# Install dependencies
make install

# Run all tests
make test

# Run specific test with verbose output
uv run pytest tests/test_file.py::test_function -v

# Manual inspector test
python tests/test_inspector.py

# Type checking
make type-check

# Code quality
make lint
make format
```

### Assistant Management
```bash
# Start assistant service
make start

# Docker operations
make docker-build
make docker-run-local
```

## Project Structure

### Core Implementation (`/assistant/`)
- `assistant.py`: Main assistant with dual-role event handling
- `config.py`: Role-specific prompt templates and configuration
- `storage.py` & `storage_models.py`: Persistent state management
- `conversation_share_link.py`: Cross-conversation linking and synchronization
- `files.py`: File synchronization via ShareFilesManager
- `respond.py`: Response generation logic
- `common.py`: Role detection and common utilities

### Agentic (`/assistant/agentic/`)
- `team_welcome.py`: Team welcome message generation
- `coordinator_support.py`: Coordinator guidance and support
- `analysis.py`: Analysis functionality

### Domain Logic (`/assistant/domain/`)
- `share_manager.py`: Share creation, joining, and cross-conversation coordination (`ShareManager` class)
- `knowledge_brief_manager.py`: Brief creation and management (`KnowledgeBriefManager` class)
- `knowledge_digest_manager.py`: Auto-updating digest system (`KnowledgeDigestManager` class)
- `learning_objectives_manager.py`: Learning goal tracking (`LearningObjectivesManager` class)
- `information_request_manager.py`: Team question handling (`InformationRequestManager` class)
- `audience_manager.py`: Audience definition and management (`AudienceManager` class)

### Tools (`/assistant/tools/`)
- `information_requests.py`: Information request handling
- `learning_objectives.py`: Learning objective management
- `learning_outcomes.py`: Outcome tracking
- `progress_tracking.py`: Transfer progress monitoring
- `share_setup.py`: Share link creation

### UI Tabs (`/assistant/ui-tabs/`)
- `brief.py`: Knowledge transfer status dashboard
- `learning.py`: Learning objectives tracking
- `sharing.py`: Sharing status monitoring
- `debug.py`: Debug information panel

### Configuration (`/assistant/text_includes/`)
Role-specific prompts and instruction templates:
- `coordinator_role.txt` & `coordinator_instructions.txt`: Coordinator mode configuration
- `team_role.txt` & `team_instructions.txt`: Team mode configuration
- `knowledge_digest_prompt.txt`: LLM prompts for digest generation

## Key Dependencies

- `semantic-workbench-assistant`: Core assistant framework
- `assistant-extensions[attachments]`: File attachment support with dashboard cards
- `content-safety`: Content moderation capabilities
- `openai-client`: LLM integration for knowledge digest generation

## Development Guidelines

### Code Philosophy
The project follows a "wabi-sabi" philosophy emphasizing:
- Ruthless simplicity with minimal abstractions
- Present-moment focus rather than future-proofing
- Trust in emergence from simple, well-defined components
- Direct library integration with minimal wrappers

### Code Style
- Use 4 spaces for indentation
- Maximum line length: 120 characters
- Follow PEP 8 naming conventions
- Use type annotations consistently
- Write docstrings for functions and classes

### Quality Assurance
Always run the full quality check before submitting changes:
```bash
make lint && make type-check && make test
```

### Important Development Notes
- Use `uv` for all Python script execution to ensure correct environment
- Keep ConversationRole enum consistent across all files
- Use Optional typing for parameters that might be None
- Update tests when changing functionality - never skip or remove tests
- Access logs in `.data/logs/` directory (timestamped, latest sorted last)
- Never make git commits - leave that to QA review process

## Testing

The test suite covers:
- Artifact loading and management (`test_artifact_loading.py`)
- Inspector functionality (`test_inspector.py`)
- File sharing and synchronization (`test_share_manager.py`)
- Storage system operations (`test_share_storage.py`)
- Tool functionality (`test_share_tools.py`)
- Team mode operations (`test_team_mode.py`)

Run tests with:
```bash
# All tests
make test

# Specific test file
uv run pytest tests/test_share_manager.py -v

# Single test function
uv run pytest tests/test_share_manager.py::test_file_sync -v
```