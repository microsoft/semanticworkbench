# Mission Assistant

A dual-mode context transfer system that facilitates collaborative missions between HQ and Field personnel in the Semantic Workbench.

## Overview

The Mission Assistant is designed to bridge the information gap between HQ planners and Field operators by providing a structured communication system with shared artifacts, real-time updates, and bidirectional information flow. It enables:

- **Mission Definition**: HQ can create detailed mission briefings with goals and success criteria
- **Information Sharing**: Knowledge transfer between separate conversations
- **Field Requests**: Field personnel can request information or assistance from HQ
- **Progress Tracking**: Real-time mission status updates and completion criteria
- **Inspector Panel**: Visual dashboard showing mission state and progress

## Key Features

### Dual Mode Operation

The assistant operates in two distinct modes with different capabilities:

1. **HQ Mode (Definition Stage)**
   - Create mission briefings with clear goals and success criteria
   - Develop a knowledge base with mission-critical information
   - Provide guidance and respond to field requests
   - Control the "Ready for Field" gate when mission definition is complete

2. **Field Mode (Working Stage)**
   - Access mission briefing and knowledge base
   - Mark success criteria as completed
   - Log requests for information or assistance from HQ
   - Update mission status with progress information
   - Report mission completion when all criteria are met

### Key Artifacts

The system manages several core artifacts that support mission operations:

- **Mission Briefing**: Details mission goals and success criteria
- **Knowledge Base**: Structured information repository for the mission
- **Field Requests**: Documented information needs from Field personnel
- **Mission Status**: Real-time progress tracking and state information

### State Management

The assistant uses a multi-layered state management approach:

- **Cross-Conversation Linking**: Connects HQ and Field conversations
- **File Synchronization**: Key artifacts are shared between conversations
- **Inspector Panel**: Real-time visual status dashboard for mission progress
- **Conversation-Specific Storage**: Each conversation maintains role-specific state

## Usage

### Commands

#### Common Commands
- `/status` - View current mission status and progress
- `/info [briefing|kb|requests|all]` - View mission information

#### HQ Commands
- `/create-mission <name> | <description>` - Create a new mission
- `/add-goal <name> | <description> | [criteria1;criteria2;...]` - Add a mission goal
- `/add-kb-section <title> | <content>` - Add knowledge base section
- `/ready-for-field` - Mark mission as ready for field operations
- `/invite` - Generate mission invitation for field personnel
- `/resolve <request-id> | <resolution>` - Resolve a field request

#### Field Commands
- `/join <invitation-code>` - Join an existing mission
- `/request-info <title> | <description> | [priority]` - Create field request
- `/update-status <status> | <progress> | <message>` - Update mission status
- `/complete-criteria <goal-index> <criteria-index>` - Mark criterion as complete
- `/complete-mission` - Report mission completion

### Workflow

1. **HQ Preparation**:
   - Create mission briefing with goals and success criteria
   - Develop knowledge base with necessary information
   - Generate invitation link for field personnel
   - Mark mission as ready for field

2. **Field Operations**:
   - Join mission using invitation link
   - Review mission briefing and knowledge base
   - Execute mission tasks and track progress
   - Create field requests when information is needed
   - Mark criteria as completed when achieved
   - Report mission completion when all goals are met

3. **Collaborative Cycle**:
   - HQ responds to field requests with information
   - Field updates mission status with progress
   - Both sides can view mission status and progress via inspector panel

## Development

### Project Structure

- `/assistant/`: Core implementation files
  - `chat.py`: Main assistant implementation with event handlers
  - `mission_tools.py`: Tool functions for the LLM to use
  - `state_inspector.py`: Inspector panel implementation
  - `mission_manager.py`: Mission state and artifact management
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

The Mission Assistant leverages the Semantic Workbench Assistant library for core functionality and extends it with:

1. **Cross-Conversation Communication**: Using the conversation sharing API
2. **Artifact Management**: Structured data models for mission information
3. **State Inspection**: Real-time mission status dashboard
4. **Tool-based Interaction**: LLM functions for mission tasks
5. **Role-Specific Experiences**: Tailored interfaces for HQ and Field roles

The system follows a centralized artifact storage model with event-driven updates to keep all conversations synchronized.

## License

Copyright (c) Microsoft. All rights reserved.