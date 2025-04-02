# Project Assistant

A dual-mode context transfer system that facilitates collaborative projects between Coordinators and Team members in the Semantic Workbench.

## Overview

The Project Assistant is designed to bridge the information gap between project Coordinators and Team members by providing a structured communication system with shared artifacts, real-time updates, and bidirectional information flow. It enables:

- **Project Definition**: Coordinators can create detailed project briefs with goals and success criteria
- **Information Sharing**: Knowledge transfer between separate conversations
- **Information Requests**: Team members can request information or assistance from Coordinators
- **Progress Tracking**: Real-time project dashboard updates and completion criteria
- **Inspector Panel**: Visual dashboard showing project state and progress

## Key Features

### Dual Mode Operation

The assistant operates in two distinct modes with different capabilities:

1. **Coordinator Mode (Planning Stage)**
   - Create project briefs with clear goals and success criteria
   - Develop a knowledge base with project-critical information
   - Provide guidance and respond to information requests
   - Control the "Ready for Working" milestone when project definition is complete

2. **Team Mode (Working Stage)**
   - Access project brief and knowledge base
   - Mark success criteria as completed
   - Log requests for information or assistance from Coordinators
   - Update project dashboard with progress information
   - Report project completion when all criteria are met

### Key Artifacts

The system manages several core artifacts that support project operations:

- **Project Brief**: Details project goals and success criteria
- **Knowledge Base**: Structured information repository for the project
- **Information Requests**: Documented information needs from Team members
- **Project Dashboard**: Real-time progress tracking and state information

### State Management

The assistant uses a multi-layered state management approach:

- **Cross-Conversation Linking**: Connects Coordinator and Team conversations
- **File Synchronization**: Key artifacts are shared between conversations
- **Inspector Panel**: Real-time visual status dashboard for project progress
- **Conversation-Specific Storage**: Each conversation maintains role-specific state

## Usage

### Commands

#### Common Commands
- `/status` - View current project status and progress
- `/info [brief|kb|requests|all]` - View project information

#### Coordinator Commands
- `/create-project <name> | <description>` - Create a new project
- `/add-goal <name> | <description> | [criteria1;criteria2;...]` - Add a project goal
- `/add-kb-section <title> | <content>` - Add knowledge base section
- `/ready-for-working` - Mark project as ready for team operations
- `/invite` - Generate project invitation for team members
- `/resolve <request-id> | <resolution>` - Resolve an information request

#### Team Commands
- `/join <invitation-code>` - Join an existing project
- `/request-info <title> | <description> | [priority]` - Create information request
- `/update-status <status> | <progress> | <message>` - Update project status
- `/complete-criteria <goal-index> <criteria-index>` - Mark criterion as complete
- `/complete-project` - Report project completion

### Workflow

1. **Coordinator Preparation**:
   - Create project brief with goals and success criteria
   - Develop knowledge base with necessary information
   - Generate invitation link for team members
   - Mark project as ready for working

2. **Team Operations**:
   - Join project using invitation link
   - Review project brief and knowledge base
   - Execute project tasks and track progress
   - Create information requests when information is needed
   - Mark criteria as completed when achieved
   - Report project completion when all goals are met

3. **Collaborative Cycle**:
   - Coordinator responds to information requests
   - Team updates project status with progress
   - Both sides can view project status and progress via inspector panel

## Development

### Project Structure

- `/assistant/`: Core implementation files
  - `chat.py`: Main assistant implementation with event handlers
  - `project_tools.py`: Tool functions for the LLM to use
  - `state_inspector.py`: Inspector panel implementation
  - `project_manager.py`: Project state and artifact management
  - `artifact_messaging.py`: Cross-conversation artifact sharing
  - `command_processor.py`: Command handling logic

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

# Linting
make lint
```

## Architecture

The Project Assistant leverages the Semantic Workbench Assistant library for core functionality and extends it with:

1. **Cross-Conversation Communication**: Using the conversation sharing API
2. **Artifact Management**: Structured data models for project information
3. **State Inspection**: Real-time project status dashboard
4. **Tool-based Interaction**: LLM functions for project tasks
5. **Role-Specific Experiences**: Tailored interfaces for Coordinator and Team roles

The system follows a centralized artifact storage model with event-driven updates to keep all conversations synchronized.

## License

Copyright (c) Microsoft. All rights reserved.