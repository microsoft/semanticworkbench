# Project Assistant Implementation Plan

## Overview

The Project Assistant is designed as a dual-mode context transfer system that facilitates knowledge transfer between different conversations in the Semantic Workbench. It provides a structured way for Coordinators to create project information and Team members to access it, with bidirectional updates and communication.

The system features a simplified invitation system using project IDs directly, comprehensive project data integrated into LLM prompts, robust UUID handling, and a complete information request lifecycle including creation and deletion.

## System Design

### Conversation Structure

The Project Assistant manages three distinct types of conversations:

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
   - Automatically set up with the team role

### Operation Modes

The Project Assistant is built as a dual-mode context transfer assistant:

1. **Coordinator Mode (Planning Stage)**:
   - Project Brief Creation: Coordinator articulates the project goals and success criteria
   - Knowledge Base Development: Collection and organization of project-critical information
   - Project Preparation: Ensuring the Knowledge Base is complete and ready for team use
   - Milestone: "Ready for Working" milestone ensures project information meets quality criteria
   - Information Request Resolution: Coordinator resolves information requests from team members

2. **Team Mode (Working Stage)**:
   - Team Operations: Team members interact with the Project KB to accomplish goals
   - Request Management: Team members create and delete requests as needed
   - Coordinator Support: Coordinator is notified of Information Requests and resolves them asynchronously
   - Progress Tracking: Team members mark criteria as completed and update status
   - Milestone: "Project Completion" milestone indicates all success criteria have been met

The system supports an iterative and asynchronous workflow where the Team's operations and the Coordinator's support activities can occur concurrently, with a dynamic dashboard to display the current project status.

### Key Architectural Features

1. **Simplified Invitation System**:
   - Uses project ID directly as the universal invitation code
   - No expiration or user restrictions on project access
   - Project ID generated automatically during Coordinator initialization
   - Team members join by simply specifying the project ID

2. **Comprehensive LLM Context**:
   - Project data (brief, dashboard, KB, requests) embedded directly in prompts
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

The Project Assistant manages several key entities:

1. **Project Brief**: A clear, concise statement of the project, including goals, success criteria, and high-level context necessary for the Team to start. Owned by Coordinator, with individual success criteria that can be marked complete by Team members.

2. **Project KB (Knowledge Base)**: The curated information necessary for the Team to carry out the project, kept up-to-date by Coordinator with clear logs of updates. Owned by Coordinator, made accessible to the Team, with content formatted in Markdown.

3. **Project Dashboard**: A dynamic representation of progress toward success, updated in real time to reflect remaining tasks, active Information Requests, and Team reports. Visible to both Coordinator and Team in the dashboard, with lifecycle tracking for project milestones.

4. **Information Requests**: A concise, prioritized list of Team needs—specifically unresolved blockers, missing information, or required resources—logged for Coordinator review and resolution. Created and deletable by Team members, resolved by Coordinator, with robust UUID-based identification.

5. **Project Log**: A chronological record of all actions and interactions during the project, including updates to the Project KB, creation and deletion of Information Requests, and progress reports from the Team. Maintained by the system, visible to both Coordinator and Team.

6. **Coordinator Conversation Storage**: A selective representation of key Coordinator conversation messages made accessible to Team members for context. Includes both user and assistant messages with metadata, limited to the most recent 50 messages to prevent excessive storage growth, with proper attribution of message sources.

## Storage Architecture

The Project Assistant leverages the Semantic Workbench Assistant library's storage capabilities to maintain project state and artifacts. The storage architecture is structured as follows:

```
projects/
├── project_id_1/
│   ├── coordinator/         # Coordinator conversation data
│   │   └── conversation_role.json  # Coordinator role information
│   ├── team_conv_id_1/      # Team conversation 1 data
│   │   └── conversation_role.json  # Team role information
│   ├── team_conv_id_2/      # Team conversation 2 data
│   │   └── conversation_role.json  # Team role information
│   └── shared/              # Shared artifacts
│       ├── project_brief/          # Project brief artifacts
│       │   └── brief.json          # Project brief data
│       ├── project_kb/             # Knowledge base content
│       │   └── kb.json             # Knowledge base sections
│       ├── project_dashboard/      # Project dashboard information
│       │   └── dashboard.json      # Current project status
│       ├── information_request/    # Information requests
│       │   ├── request_id_1.json   # Individual request files
│       │   └── request_id_2.json   # Each with a unique UUID
│       ├── project_log/            # Project event log
│       │   └── log.json            # Chronological event log
│       └── coordinator_conversation/ # Coordinator conversation storage
│           └── coordinator_conversation.json # Recent messages for team access
└── project_id_2/
    └── ...
```

Key implementation details:
- Using the assistant library's `storage_directory_for_context()` to generate unique storage paths
- Storing Pydantic models via the library's `read_model()` and `write_model()` functions
- Each project gets a unique folder with subfolders for each participant conversation
- Role information stored in conversation-specific directories
- Shared folder contains artifacts accessible across all conversations in the project
- Information requests stored as individual files with UUID-based filenames
- Coordinator conversation messages stored in a centralized JSON file for team access
- Project log maintained as a single growing JSON file with chronological entries
- Clean separation between conversation-specific and shared project data

## Role-Based Behavior

The project assistant provides a customized experience based on whether the user is in Coordinator or Team mode:

### Coordinator Role (Planning Stage)

- Creates and updates the Project Brief with goals and success criteria
- Develops and refines the Project KB with project-critical information
- Shares the Project ID directly with Team members for easy access
- Has control over what information is included in the Project KB
- Receives and resolves Information Requests from team members
- Sees all active requests from all team members with their priorities
- Controls the "Ready for Working" milestone transition
- Receives notifications when team members delete their requests
- Gets comprehensive project data directly in the LLM prompt context

### Team Role (Working Stage)

- Works with the Project KB provided by Coordinator
- Creates Information Requests when encountering information gaps or blockers
- Deletes Information Requests that are no longer needed
- Joins projects directly using the project ID
- Views requests from other team members in read-only mode
- Reports on progress and findings
- Updates Project Dashboard with completed tasks
- Marks individual success criteria as completed
- Views recent Coordinator conversations for context
- Gets comprehensive project data directly in the LLM prompt context

## Data Models

Five key entity types provide the foundation for project communication:

1. **Project Brief**:
   - Project name and description
   - Goals with priority levels
   - Success criteria with completion tracking
   - Individual criterion completion with timestamp and attribution
   - Version tracking for modifications

2. **Project KB**:
   - Structured sections with titles and content
   - Tagging system for organization
   - Version tracking for updates
   - Order-based section arrangement
   - Content formatting with Markdown support

3. **Project Dashboard**:
   - Overall progress percentage tracking (0-100%)
   - Current state (planning, ready_for_working, in_progress, completed, aborted)
   - Next actions and blockers
   - Success criteria count tracking
   - Lifecycle metadata for milestone transitions
   - Attribution of state changes

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
   - Events for milestone transitions, request handling, and KB updates
   - Request deletion tracking

6. **Coordinator Conversation Storage**:
   - Shared access to Coordinator conversation for team members
   - Content and sender metadata preservation
   - Limited message history with automatic pruning
   - Read-only access for team members
