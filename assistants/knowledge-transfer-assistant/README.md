# Knowledge Transfer Assistant

A dual-mode context transfer system that facilitates collaborative knowledge sharing between Coordinators and Team members in the Semantic Workbench.

## Overview

The Knowledge Transfer Assistant is designed to bridge the information gap between project Coordinators and Team members by providing a structured communication system with shared artifacts, real-time updates, and bidirectional information flow. It enables:

- **Knowledge Organization**: Coordinators can structure and organize complex information for sharing
- **Dual-Mode Operation**: Single assistant with context-aware Coordinator and Team modes
- **Information Sharing**: Knowledge transfer between separate conversations with automatic synchronization
- **Information Requests**: Bidirectional communication system for team member questions
- **Progress Tracking**: Real-time project dashboard updates and completion tracking
- **Inspector Panels**: Multiple specialized visual dashboards showing project state, learning objectives, and debug information

## Key Features

### Conversation Types and Dual Mode Operation

The Knowledge Transfer Assistant creates and manages three distinct types of conversations:

1. **Coordinator Conversation**: The personal conversation used by the project coordinator/owner to create and manage the knowledge base.

2. **Shareable Team Conversation**: A template conversation that's automatically created along with a share URL. This conversation is never directly used - it serves as the template for creating individual team conversations when users click the share link.

3. **Team Conversation(s)**: Individual conversations for team members, created when they redeem the share URL. Each team member gets their own personal conversation connected to the project.

The assistant operates in two distinct modes with different capabilities:

1. **Coordinator Mode**
   - Create and organize knowledge briefs with learning objectives
   - Maintain an auto-updating knowledge digest with critical information
   - Provide guidance and respond to information requests
   - Share files and context with team members
   - Manage project completion tracking

2. **Team Mode**
   - Access project brief and knowledge digest
   - Request information or assistance from Coordinators
   - Update project status with progress information
   - Synchronize shared files from the coordinator
   - Explore project context and learning objectives

### Key Artifacts

The system manages several core artifacts that support knowledge transfer operations:

- **Project Brief**: Details knowledge goals and success criteria
- **Knowledge Digest**: Dynamically updated information repository that captures key project context
- **Learning Objectives**: Structured goals with specific learning outcomes
- **Information Requests**: Documented information needs from Team members with priority levels
- **Project Dashboard**: Real-time progress tracking and state information across multiple inspector panels

### State Management

The assistant uses a multi-layered state management approach:

- **Cross-Conversation Linking**: Connects Coordinator and Team conversations
- **File Synchronization**: Automatic file sharing between conversations, including when files are uploaded by Coordinators or when team members return to a conversation
- **Inspector Panel**: Real-time visual status dashboard for project progress
- **Conversation-Specific Storage**: Each conversation maintains role-specific state

## Usage

### Commands

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

### Workflow

1. **Coordinator Preparation**:
   - Create knowledge brief with learning objectives and outcomes
   - The knowledge digest automatically updates with key information from conversations
   - Share invitation link with team members
   - Upload relevant files for team access
   - Define project audience and organize knowledge structure

2. **Team Operations**:
   - Join project using invitation link
   - Review project brief and knowledge digest content
   - Request additional information with priority levels
   - Update project status with progress information
   - Synchronize files from coordinator automatically

3. **Collaborative Cycle**:
   - Coordinator responds to information requests with detailed resolutions
   - Team updates project status with progress tracking
   - Both sides can view project status and progress via multiple inspector panels
   - Real-time synchronization of project state across all conversations

## Development

### Project Structure

- `/assistant/`: Core implementation files
  - `assistant.py`: Main assistant implementation with dual-role event handling
  - `command_processor.py`: Command handling logic with role-based authorization
  - `manager.py`: Project state and artifact management (KnowledgeTransferManager)
  - `conversation_share_link.py`: Cross-conversation linking and synchronization
  - `storage.py` & `storage_models.py`: Persistent state management
  - `config.py`: Role-specific prompt templates and configuration
  - `tools.py`: Assistant tools and LLM functions
  - `files.py`: File synchronization and management (ShareManager)
  - `notifications.py`: Cross-conversation notification system
  - `data.py`: Data models for project entities
  - `conversation_clients.py`: Conversation client management
  - `analysis.py`: Analysis functionality
  - `team_welcome.py`: Team welcome message generation
  - `utils.py`: General utility functions
  - `string_utils.py`: String utility functions
  - `common.py`: Common utilities and role detection
  - `respond.py`: Response generation
  - `logging.py`: Logging configuration
  - `inspectors/`: Inspector panel components
    - `brief.py`: Brief inspector for knowledge transfer status
    - `learning.py`: Learning objectives inspector
    - `sharing.py`: Sharing status inspector
    - `debug.py`: Debug inspector
    - `common.py`: Common inspector utilities
  - `text_includes/`: Role-specific prompts and instruction templates
  - `assets/`: SVG icons and visual assets

- `/docs/`: Documentation files
  - `DESIGN.md`: System design and architecture
  - `DEV_GUIDE.md`: Development guidelines
  - `JTBD.md`: Jobs-to-be-done analysis
  - `ASSISTANT_LIBRARY_NOTES.md`: Notes on the assistant library
  - `WORKBENCH_NOTES.md`: Workbench state management details
  - `notable_claude_conversations/`: Archived design conversations

- `/tests/`: Comprehensive test suite
  - `test_artifact_loading.py`: Artifact loading and management tests
  - `test_inspector.py`: State inspector functionality tests
  - `test_share_manager.py`: File sharing and synchronization tests
  - `test_share_storage.py`: Storage system tests
  - `test_share_tools.py`: Tool functionality tests
  - `test_team_mode.py`: Team mode operation tests

### Development Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Single test with verbose output
uv run pytest tests/test_file.py::test_function -v

# Manual inspector test
python tests/test_inspector.py

# Type checking
make type-check

# Linting and formatting
make lint
make format

# Docker operations
make docker-build
make docker-run-local

# Start assistant service
make start
```

## Architecture

The Knowledge Transfer Assistant leverages the Semantic Workbench Assistant library and extends it with:

### Key Dependencies
- `semantic-workbench-assistant`: Core assistant framework
- `assistant-extensions[attachments]`: File attachment support with dashboard cards
- `content-safety`: Content moderation capabilities
- `openai-client`: LLM integration for knowledge digest generation

### Architectural Components
1. **Cross-Conversation Communication**: Advanced conversation sharing and synchronization
2. **Artifact Management**: Structured data models for briefs, objectives, and requests
3. **Multi-Panel State Inspection**: Specialized inspector panels for different project aspects
4. **Tool-based Interaction**: Comprehensive LLM functions for project operations
5. **Role-Specific Experiences**: Context-aware interfaces for Coordinator and Team modes
6. **Auto-Updating Knowledge Digest**: LLM-powered automatic extraction of key information
7. **File Synchronization**: Automatic file sharing and synchronization across conversations

### Design Philosophy
The system follows a **wabi-sabi philosophy** emphasizing:
- Ruthless simplicity with minimal abstractions
- Present-moment focus rather than future-proofing
- Trust in emergence from simple, well-defined components
- Direct library integration with minimal wrappers
- Pragmatic trust in external systems

The architecture uses a centralized artifact storage model with event-driven updates and real-time UI synchronization to keep all conversations coordinated.
