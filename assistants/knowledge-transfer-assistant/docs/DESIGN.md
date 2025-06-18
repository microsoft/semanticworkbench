# Knowledge Transfer Assistant Implementation Design

## Overview

The Knowledge Transfer Assistant is a dual-role context transfer system that facilitates knowledge sharing between conversations in the Semantic Workbench. Coordinators organize and share information with team members through bidirectional communication, automatic knowledge synthesis, and real-time collaboration.

## System Design

### Core Architecture

- **Service Name**: Knowledge Transfer Assistant
- **Service ID**: `knowledge-transfer-assistant.made-exploration`
- **Primary Function**: File-sharing mediation and collaborative knowledge sharing
- **Architecture**: Dual-role system with coordinator and team member modes

### Conversation Structure

The assistant manages three conversation types:

1. **Coordinator Conversation**
   - Personal workspace for knowledge organizers
   - Contains private coordinator-assistant communication
   - Stores shareable team conversation link
   - Maintains auto-updating whiteboard from conversation content

2. **Shareable Team Conversation**
   - Template conversation with share URL
   - Never directly used - serves as template only
   - Team members get copies when clicking share links
   - Pre-configured with team member role and shared knowledge access

3. **Team Conversation(s)**
   - Individual conversations for each team member
   - All linked to same knowledge transfer project
   - Used for knowledge exploration and information requests
   - Auto-configured with team member role and shared artifacts

### Assistant Roles

#### Coordinator Role

- Knowledge organization and structuring
- Auto-updating whiteboard management
- Information request resolution
- File and context sharing
- Project brief creation with goals and success criteria
- Full visibility of team member requests and interactions

#### Team Member Role

- Knowledge exploration through structured whiteboard
- Information request creation
- File synchronization from coordinators
- Progress tracking and success criteria completion
- Coordinator conversation context access
- Self-paced knowledge discovery

### Key Architectural Features

1. **Invitation System**
   - Uses Semantic Workbench conversation sharing
   - Coordinators share redeemable URLs out-of-band
   - Each team member gets own conversation copy linked to project

2. **LLM Context Integration**
   - Project data (brief, whiteboard, requests) embedded in prompts
   - Role-specific formatting for each user type
   - Dynamic information request listing with ID formatting
   - Content truncation for context length management

3. **Information Request Management**
   - Complete lifecycle: creation → resolution
   - UUID handling with multiple matching strategies
   - Conversation-based ownership controls
   - Role-appropriate visibility (coordinators see all, team members read-only)

4. **Automatic Knowledge Synthesis**
   - Auto-updating whiteboard from coordinator conversations
   - AI-powered content organization
   - Token-limited content (~2500 tokens)
   - Markdown formatting
   - No manual maintenance required

5. **Cross-Conversation Communication**
   - Coordinator conversation sharing with team members
   - Centralized JSON file storage for team access
   - Automatic message capture (user and assistant)
   - Metadata preservation (sender, timestamps)
   - 50-message limit to prevent storage growth

## Data Architecture

### Core Data Models

#### Project Brief

- Knowledge transfer goals and objectives
- Success criteria with completion tracking
- Timeline and context scope
- Version tracking

#### Project Whiteboard

- Auto-updated knowledge repository
- AI synthesis of coordinator conversation content
- Markdown formatting
- Version tracking with timestamps
- Content truncation (~2500 tokens)
- Updates after each coordinator assistant message

#### Project Info

- Project identifier and name
- State tracking (planning, in_progress, completed, etc.)
- Coordinator and team conversation ID references
- Shareable invitation URL
- Status messages and notes
- Creation/update timestamps

#### Information Requests

- Priority levels (low, medium, high, critical)
- Status tracking (new, acknowledged, in_progress, resolved, deferred)
- Lifecycle management (creation, updates, resolution)
- UUID-based identification with flexible matching
- Resolution information and update history
- Conversation-based ownership controls

#### Project Log

- Chronological event record
- Event categorization with specialized types
- User and conversation attribution
- Event context metadata
- Milestone transitions, request handling, whiteboard updates
- Request deletion tracking

#### Coordinator Conversation Storage

- Team member access to coordinator conversation context
- Content and sender metadata preservation
- 50-message limit with automatic pruning
- Both user and assistant messages included
- Enables team understanding of coordinator reasoning

## Storage Architecture

### Directory Structure

```text
projects/
├── project_id_1/
│   ├── linked_conversations/         # Conversation linkage tracking
│   │   ├── conversation_id_1         # Empty file - presence indicates linkage
│   │   ├── conversation_id_2         # Empty file for another linked conversation
│   │   └── ...                       # One file per linked conversation
│   ├── requests/                     # Information requests
│   │   ├── request_id_1.json         # Individual request files with UUID names
│   │   └── request_id_2.json         # Each request stored independently
│   ├── project.json                  # Core project information and metadata
│   ├── brief.json                    # Knowledge transfer brief and goals
│   ├── whiteboard.json               # Auto-updated knowledge content
│   ├── log.json                      # Chronological event log
│   └── coordinator_conversation.json # Recent coordinator messages for team access
└── project_id_2/
    └── ...
```

### Conversation-Specific Storage

```text
.data/assistants/{assistant_id}/conversations/{conversation_id}/
├── project_role.json         # Role: coordinator or team
└── project_association.json  # Associated project ID
```

### Implementation Details

#### Storage Technology

- File-based JSON storage using Pydantic models
- Path management through `pathlib.Path`
- Semantic Workbench Assistant library storage utilities
- Configurable base directory via `settings.storage.root`
- No external database dependencies

#### Data Management

- Unique project folders containing all shared data
- Conversation roles and associations in conversation-specific storage
- Empty files in linked_conversations/ directory for linkage tracking
- UUID-based filenames for information requests
- AI-processed conversation content for whiteboard updates
- Centralized coordinator messages with 50-message limit
- Single growing JSON file for project logs

#### Performance and Reliability

- Atomic read/write operations for individual files
- Error handling with optional return types
- Directory-based conversation linking
- Token limiting for whiteboard content
- Message limiting for coordinator conversations

## Role-Based Behavior

### Coordinator Capabilities

- Project brief creation with goals and success criteria
- Auto-updating whiteboard through AI conversation analysis
- Information request resolution from team members
- File and resource sharing with team access
- Project URL sharing for team member access
- All team member request visibility with priority levels
- Team member activity and request status notifications
- Project data embedded in LLM prompt context

### Team Member Capabilities

- Whiteboard access with auto-updates from coordinator conversations
- Information request creation for gaps or blockers
- Information request deletion when no longer needed
- Project access via coordinator-provided share URLs
- Read-only visibility of other team member requests
- Progress reporting and completion status updates
- Success criteria completion marking with timestamps
- Coordinator conversation context access for background
- Automatic file and resource access from coordinators
- Project data embedded in LLM prompt context

## Command System

### General Commands (All Users)

- `/help [command]` - Context-sensitive help
- `/project-info [brief|whiteboard|status|requests]` - View project information

### Coordinator Commands

- `/create-brief` - Create knowledge transfer brief
- `/add-goal` - Add goals with success criteria
- `/resolve-request` - Resolve team member information requests
- `/list-participants` - List all project participants

### Team Commands

- `/request-info` - Create prioritized information requests
- `/update-status` - Update project status and progress
- `/sync-files` - Synchronize shared files from coordinator

### Authorization

- Role-based command restrictions (coordinator vs team)
- Error messages for unauthorized access attempts
- Role detection via conversation metadata with file storage backup
- Role-specific command visibility in help

## User Interface Integration

### State Inspector Panel

- Real-time project status dashboard
- Information composition from multiple data entities
- Progress tracking and completion status visualization
- Information request status and priority visualization
- Project timeline and milestone tracking
- Cross-conversation activity summaries

### Real-Time Synchronization

- Automatic UI updates after data modifications
- `AssistantStateEvent` for cross-conversation UI synchronization
- Efficient refresh patterns
- Consistent state representation across linked conversations

## Technical Implementation

The system provides knowledge transfer and collaborative information sharing functionality through file-based storage, role-based access control, automatic content synthesis, and real-time cross-conversation synchronization.
