# Knowledge Transfer Assistant

A file-sharing mediator assistant that facilitates collaborative knowledge sharing between Coordinators and Team members in the Semantic Workbench.

## Overview

The Knowledge Transfer Assistant is designed to bridge the information gap between project Coordinators and Team members by providing a structured communication system with shared artifacts, real-time updates, and bidirectional information flow. It enables:

- **Knowledge Organization**: Coordinators can structure and organize complex information for sharing
- **Information Sharing**: Knowledge transfer between separate conversations
- **Information Requests**: Team members can request information or assistance from Coordinators
- **Progress Tracking**: Real-time project dashboard updates and completion tracking
- **Inspector Panel**: Visual dashboard showing project state and progress

## Key Features

### Conversation Types and Dual Mode Operation

The Knowledge Transfer Assistant creates and manages three distinct types of conversations:

1. **Coordinator Conversation**: The personal conversation used by the project coordinator/owner to create and manage the knowledge base.

2. **Shareable Team Conversation**: A template conversation that's automatically created along with a share URL. This conversation is never directly used - it serves as the template for creating individual team conversations when users click the share link.

3. **Team Conversation(s)**: Individual conversations for team members, created when they redeem the share URL. Each team member gets their own personal conversation connected to the project.

The assistant operates in two distinct modes with different capabilities:

1. **Coordinator Mode**
   - Create and organize knowledge briefs
   - Maintain an auto-updating project whiteboard with critical information
   - Provide guidance and respond to information requests
   - Share files and context with team members

2. **Team Mode**
   - Access project brief and project whiteboard
   - Request information or assistance from Coordinators
   - Update project status with progress information
   - Synchronize shared files from the coordinator

### Key Artifacts

The system manages several core artifacts that support knowledge transfer operations:

- **Project Brief**: Details knowledge goals and success criteria
- **Project Whiteboard**: Dynamically updated information repository that captures key project context
- **Information Requests**: Documented information needs from Team members
- **Project Dashboard**: Real-time progress tracking and state information

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
- `/project-info [brief|whiteboard|status|requests]` - View project information

#### Coordinator Commands

- `/create-brief` - Create a knowledge brief
- `/add-goal` - Add a goal with success criteria
- `/resolve-request` - Resolve an information request from team members
- `/list-participants` - List all project participants

#### Team Commands

- `/request-info` - Request information or assistance from the Coordinator
- `/update-status` - Update project status and progress
- `/sync-files` - Synchronize shared files from the project

### Workflow

1. **Coordinator Preparation**:
   - Create knowledge brief with goals and context
   - The project whiteboard automatically updates with key information
   - Share invitation link with team members
   - Upload relevant files for team access

2. **Team Operations**:
   - Join project using invitation link
   - Review project brief and whiteboard content
   - Request additional information when needed
   - Update project status with progress
   - Synchronize files from coordinator

3. **Collaborative Cycle**:
   - Coordinator responds to information requests
   - Team updates project status with progress
   - Both sides can view project status and progress via inspector panel

## Development

### Project Structure

- `/assistant/`: Core implementation files
  - `assistant.py`: Main assistant implementation with event handlers
  - `command_processor.py`: Command handling logic with role-based authorization
  - `state_inspector.py`: Inspector panel implementation
  - `manager.py`: Project state and artifact management
  - `conversation_project_link.py`: Cross-conversation linking and synchronization
  - `storage.py` & `storage_models.py`: Persistent state management
  - `config.py`: Role-specific prompt templates and configuration
  - `tools.py`: LLM tool functions for project operations
  - `files.py`: File synchronization and management
  - `notifications.py`: Cross-conversation notification system

- `/docs/`: Documentation files
  - `DESIGN.md`: System design and architecture
  - `DEV_GUIDE.md`: Development guidelines
  - `ASSISTANT_LIBRARY_NOTES.md`: Notes on the assistant library
  - `WORKBENCH_NOTES.md`: Workbench state management details

- `/tests/`: Test files covering key functionality

### Development Commands

```bash
# Install dependencies
make install

# Run tests
make test

# Type checking
make type-check

# Linting and formatting
make lint
make format
```

## Architecture

The Knowledge Transfer Assistant leverages the Semantic Workbench Assistant library for core functionality and extends it with:

1. **Cross-Conversation Communication**: Using the conversation sharing API
2. **Artifact Management**: Structured data models for project information
3. **State Inspection**: Real-time project status dashboard
4. **Tool-based Interaction**: LLM functions for project tasks
5. **Role-Specific Experiences**: Tailored interfaces for Coordinator and Team roles

The system follows a centralized artifact storage model with event-driven updates to keep all conversations synchronized.
