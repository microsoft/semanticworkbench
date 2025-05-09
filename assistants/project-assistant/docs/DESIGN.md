# Project Assistant Implementation Plan

## Overview

The Project Assistant is designed as a dual-role context transfer system that facilitates knowledge transfer between different conversations in the Semantic Workbench. It provides a structured way for Coordinators to create project information and Team members to access it, with bidirectional updates and communication.

## System Design

### Configuration Templates

The Project Assistant supports two different configuration templates within a unified codebase. The templates modify the behavior of the assistants considerably, so we basically have two different assistants with this single assistant codebase.

1. **Default Template (Project Assistant)**:
   - Full project management capabilities with tracking features
   - Includes goals, success criteria, and project state monitoring
   - Tracks progress of project tasks and completion status
   - Uses "Project Assistant" branding and terminology
   - Provides comprehensive project dashboard with status tracking
   - Focuses on project management workflow with sequential stages

2. **Context Transfer Template (Context Transfer Assistant)**:
   - Simplified knowledge sharing without project tracking features
   - Designed for knowledge transfer without formal project structure
   - No goals or success criteria tracking
   - Uses "Context Transfer Assistant" branding and terminology
   - Maintains core information request capabilities without project stages
   - Different welcome messages and UI labels appropriate for knowledge sharing

The system automatically adapts its behavior, prompts, and UI based on which template is selected during assistant instantiation, while maintaining a unified codebase and consistent architecture.

Some features remain in both assistant configurations:

- Both assistants maintain a "whiteboard" internally to build up context of the project (the "project" for the Context Transfer Assistant is to transfer the context well, while for the Project Assistant it is a project in a more formal sense). The whiteboard is updated by the assistant each time they reply to the user. The whiteboard is distinct from the project information dashboard which is a collaboration between the user and the assistant.
- Both assistants syncronize project information and files between coordinators and team members.
- Both assistants facilitate the creation of information requests by team members, and the answering of information requests by the coordinators.
- Both assistants can speak conversationally and run their own sets of tools.

### Conversation Structure

The Project Assistant (in both configurations) manages three distinct types of conversations:

1. **Coordinator Conversation**:
   - Created when a user first interacts with the Project Assistant
   - Acts as the personal workspace for the project owner/coordinator
   - Contains private communication between the coordinator and the assistant
   - Stores the link to the shareable team conversation
   - Used for high-level project management and planning

2. **Shareable Team Conversation**:
   - Automatically created when a coordinator starts a new project
   - Never directly used by any user - serves as a template only
   - Has a share URL associated with it
   - When team members click the share link, they get a copy of this conversation
   - Contains project-specific setup and metadata

3. **Team Conversation(s)**:
   - Created when a team member redeems the share URL
   - Each team member gets their own personal conversation
   - All team conversations are linked to the same project
   - Used for team members to work on the project, make information requests, etc.
   - Automatically set up with the team member role

### Conversation Roles

Within each configuration template, the Project Assistant supports two distinct conversation roles:

1. **Coordinator Role**:
   - Knowledge Base Development: Collection and organization of project-critical information
   - Information Request Resolution: Coordinator resolves information requests from team members
   - **In Default Template**:
     - Project Brief Creation with goals and success criteria
     - Project Preparation with staged milestones
     - "Ready for Working" milestone management
   - **In Context Transfer Template**:
     - Knowledge organization without formal project stages
     - Focus on information structuring without tracking progress

2. **Team Member Role**:
   - Information Access: Team members interact with the shared Knowledge Base
   - Request Management: Team members create and delete information requests as needed
   - **In Default Template**:
     - Progress Tracking with criteria completion
     - Dashboard updates with completion status
     - Support for "Project Completion" milestone
   - **In Context Transfer Template**:
     - Knowledge exploration without progress tracking
     - Information requests without formal project stages

For both configuration templates, the system supports an iterative and asynchronous workflow where the team members' operations and the coordinator's support activities can occur concurrently. The default template provides a comprehensive project dashboard with status tracking, while the context transfer template focuses on knowledge exchange without formal project stages.

### Key Architectural Features

1. **Simplified Invitation System**:
   - Uses Semantic Workbench features to clone new team conversations from shareable conversations. The coordinator gives the team members redeemable share links out-of-band.

2. **Comprehensive LLM Context**:
   - Project data (brief, info, whiteboard, requests) embedded directly in prompts
   - Role-specific formatting to highlight relevant information
   - Dynamic listing of information requests with proper ID formatting
   - Intelligent truncation to manage context length
   - Improves response quality by reducing the need for tool calls

3. **Robust Information Request Management**:
   - Complete lifecycle from creation to deletion
   - Enhanced UUID handling with multiple matching strategies
   - Conversation-based ownership controls
   - Role-appropriate visibility of requests
   - Proper notification for all parties

4. **Coordinator Conversation Sharing**:
   - Selective Coordinator conversation message sharing with team members
   - Storage in a centralized JSON file for all team members to access
   - Automatic capture of both user and assistant messages
   - Metadata preservation including sender name and timestamp
   - Limited to recent messages (last 50) to prevent excessive storage
   - Read-only access via the `view_coordinator_conversation` tool for team members
   - Team members can view Coordinator discussions for better context awareness

## Data

The Project Assistant manages several key entities that work together to provide a cohesive experience:

1. **Project Brief**: A clear, concise statement of the project, including goals, success criteria, and high-level context necessary for the Team to start. Owned by Coordinator, with individual success criteria that can be marked complete by Team members.

2. **Project Whiteboard**: A dynamic, automatically updated knowledge repository that captures key information from conversations. The whiteboard is continuously updated as the coordinator interacts with the assistant, extracting and organizing essential project context. It's formatted in Markdown and made available to all team members without requiring manual maintenance.

3. **Project Info**: Core metadata and state information about the project, including its unique ID, name, current lifecycle state, conversation IDs, share URL, and status messages. This model serves as the central reference point for project identification and collaboration settings. It replaced the previous dashboard entity to eliminate duplication and provide cleaner separation between data and UI.

4. **Information Requests**: A concise, prioritized list of Team needs—specifically unresolved blockers, missing information, or required resources—logged for Coordinator review and resolution. Created and deletable by Team members, resolved by Coordinator, with robust UUID-based identification.

5. **Project Log**: A chronological record of all actions and interactions during the project, including updates to the project whiteboard, creation and deletion of information requests, and progress reports from the team. Maintained by the system, visible to both coordinator and team members.

6. **Coordinator Conversation Storage**: A selective representation of key Coordinator conversation messages made accessible to Team members for context. Includes both user and assistant messages with metadata, limited to the most recent 50 messages to prevent excessive storage growth, with proper attribution of message sources.

The State Inspector UI component (visible tab in the Semantic Workbench) dynamically composes information from these entities to present a unified view, rather than relying on a single "dashboard" entity. This decoupling of data from UI allows for more flexible presentation and eliminates redundancy.

## Storage Architecture

The Project Assistant leverages the Semantic Workbench Assistant library's storage capabilities to maintain project state and artifacts. The storage architecture is structured as follows:

```
projects/
├── project_id_1/
│   ├── linked_conversations/         # Directory tracking all linked conversations
│   │   ├── conversation_id_1         # Empty file - just presence indicates linkage
│   │   ├── conversation_id_2         # Empty file for another linked conversation
│   │   └── ...                       # One file per linked conversation
│   ├── requests/                     # Information requests directory
│   │   ├── request_id_1.json         # Individual request files
│   │   └── request_id_2.json         # Each with a unique UUID
│   ├── project.json                  # Core project information
│   ├── brief.json                    # Brief data
│   ├── whiteboard.json               # Automatically updated knowledge content
│   ├── log.json                      # Chronological event log
│   └── coordinator_conversation.json # Recent coordinator messages for team access
└── project_id_2/
    └── ...
```

Additionally, conversation-specific data is stored in the assistant library's context-specific storage. This provides the mechanism for the assistant to know which project it is a part of:

```
.data/assistants/{assistant_id}/conversations/{conversation_id}/
├── project_role.json         # Role of this conversation (coordinator or team)
└── project_association.json  # Project this conversation is associated with
```

Key implementation details:

- Using the assistant library's `storage_directory_for_context()` to generate unique storage paths
- Storing Pydantic models via the library's `read_model()` and `write_model()` functions
- Each project gets a unique folder containing all shared project data
- Conversation roles and project associations tracked in conversation-specific storage
- Linked conversations tracked with empty files in a special directory
- Information requests stored as individual files with UUID-based filenames
- Auto-updating whiteboard maintained with AI-processed conversation content
- Coordinator conversation messages stored centrally with a maximum of 50 recent messages
- Project log maintained as a single growing JSON file with chronological entries
- Clean separation between conversation-specific and shared project data

## Role-Based Behavior

The project assistant provides a customized experience based on whether the user is in Coordinator or Team mode:

### Coordinator Role

- Creates and updates the Project Brief with goals and success criteria
- Contributes to the auto-updating Project Whiteboard through conversations
- Shares a unique project URL with team members for easy access
- Receives and resolves Information Requests from team members
- Sees all active requests from all team members with their priorities
- Controls milestone transitions (in default template)
- Receives notifications when team members delete their requests
- Gets comprehensive project data directly in the LLM prompt context

### Team Member Role

- Works with the Project Whiteboard that's automatically updated based on coordinator conversations
- Creates Information Requests when encountering information gaps or blockers
- Deletes Information Requests that are no longer needed
- Joins projects by redeeming the share URL provided by the coordinator
- Views requests from other team members in read-only mode
- Reports on progress and findings
- Marks individual success criteria as completed (in default template)
- Views recent coordinator conversations for additional context
- Gets comprehensive project data directly in the LLM prompt context

## Data Models

Five key entity types provide the foundation for project communication:

1. **Project Brief**:
   - Project name and description
   - Goals with priority levels
   - Success criteria with completion tracking
   - Individual criterion completion with timestamp and attribution
   - Version tracking for modifications

2. **Project Whiteboard**:
   - Dynamically generated and auto-updated content
   - AI-powered synthesis of conversation content
   - Simplified Markdown formatting for readability
   - Version tracking with timestamps
   - Automatic organization of key information
   - Content truncation to maintain manageable size (limited to ~2000 tokens)
   - Updated after each assistant message in coordinator conversations

3. **Project Info**:
   - Unique project identifier and name
   - Current project state tracking (planning, ready_for_working, in_progress, completed, aborted)
   - Coordinator and team conversation IDs
   - Shareable invitation URL for team members
   - Status messages and custom project notes
   - Creation and update timestamps
   - Serves as the central reference for project metadata
   - Replaced previous dashboard entity to decouple data from UI

4. **Information Requests**:
   - Prioritized information needs (low, medium, high, critical)
   - Status tracking (new, acknowledged, in_progress, resolved, deferred)
   - Complete request lifecycle (creation, deletion)
   - UUID-based identification with flexible matching
   - Resolution information and update history
   - Conversation-based ownership controls

5. **Project Log**:
   - Chronological record of all events
   - Rich categorization system with specialized entry types
   - Attribution of actions to specific users
   - Metadata for event context
   - Events for milestone transitions, request handling, and whiteboard updates
   - Request deletion tracking
   - Full history of all project activities

6. **Coordinator Conversation Storage**:
   - Shared access to coordinator conversation for team members
   - Content and sender metadata preservation
   - Limited message history (most recent 50 messages)
   - Automatic pruning of older messages
   - Read-only access for team members via the `view_coordinator_conversation` tool
   - Includes both user and assistant messages
