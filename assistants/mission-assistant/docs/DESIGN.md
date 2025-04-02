# Mission Assistant Implementation Plan

## Overview

The Mission Assistant is designed as a dual-mode context transfer system that facilitates knowledge transfer between different conversations in the Semantic Workbench. It provides a structured way for HQ to create mission information and Field personnel to access it, with bidirectional updates and communication.

The system features a simplified invitation system using mission IDs directly, comprehensive mission data integrated into LLM prompts, robust UUID handling, and a complete field request lifecycle including creation and deletion.

## System Design

The Mission Assistant is built as a dual-mode context transfer assistant:

1. **HQ Mode (Definition Stage)**:
   - Mission Briefing Creation: HQ articulates the mission goals and success criteria
   - Knowledge Base Development: Collection and organization of mission-critical information
   - Mission Preparation: Ensuring the Knowledge Base is complete and ready for field use
   - Gate: "Ready for Field" checkpoint ensures mission information meets quality criteria
   - Field Request Resolution: HQ resolves information requests from field agents

2. **Field Mode (Working Stage)**:
   - Field Operations: Field personnel interact with the Mission KB to accomplish goals
   - Request Management: Field agents create and delete requests as needed
   - HQ Support: HQ is notified of Field Requests and resolves them asynchronously
   - Progress Tracking: Field agents mark criteria as completed and update status
   - Gate: "Mission Completion" checkpoint indicates all success criteria have been met

The system supports an iterative and asynchronous workflow where the Field's operations and the HQ's support activities can occur concurrently, with a dynamic information radiator to display the current mission status.

### Key Architectural Features

1. **Simplified Invitation System**:
   - Uses mission ID directly as the universal invitation code
   - No expiration or user restrictions on mission access
   - Mission ID generated automatically during HQ initialization
   - Field agents join by simply specifying the mission ID

2. **Comprehensive LLM Context**:
   - Mission data (briefing, status, KB, requests) embedded directly in prompts
   - Role-specific formatting to highlight relevant information
   - Dynamic listing of field requests with proper ID formatting
   - Intelligent truncation to manage context length
   - Improves response quality by reducing the need for tool calls

3. **Robust Field Request Management**:
   - Complete lifecycle from creation to deletion
   - Enhanced UUID handling with multiple matching strategies
   - Conversation-based ownership controls
   - Role-appropriate visibility of requests
   - Proper notification for all parties

4. **HQ Conversation Sharing**:
   - Selective HQ conversation message sharing with field agents
   - Storage in a centralized JSON file for all field agents to access
   - Automatic capture of both user and assistant messages
   - Metadata preservation including sender name and timestamp
   - Limited to recent messages (last 50) to prevent excessive storage
   - Read-only access via the `view_hq_conversation` tool for field agents
   - Field agents can view HQ discussions for better context awareness

## Data

The Mission Assistant manages several key entities:

1. **Mission Briefing**: A clear, concise statement of the mission, including goals, success criteria, and high-level context necessary for the Field to start. Owned by HQ, with individual success criteria that can be marked complete by Field agents.

2. **Mission KB (Knowledge Base)**: The curated information necessary for the Field to carry out the mission, kept up-to-date by HQ with clear logs of updates. Owned by HQ, made accessible to the Field, with content formatted in Markdown.

3. **Mission Status**: A dynamic representation of progress toward success, updated in real time to reflect remaining tasks, active Field Requests, and Field reports. Visible to both HQ and Field in the information radiator, with lifecycle tracking for mission gates.

4. **Field Requests**: A concise, prioritized list of Field needs—specifically unresolved blockers, missing information, or required resources—logged for HQ review and resolution. Created and deletable by Field agents, resolved by HQ, with robust UUID-based identification.

5. **Mission Log**: A chronological record of all actions and interactions during the mission, including updates to the Mission KB, creation and deletion of Field Requests, and progress reports from the Field. Maintained by the system, visible to both HQ and Field.

6. **HQ Conversation Storage**: A selective representation of key HQ conversation messages made accessible to Field agents for context. Includes both user and assistant messages with metadata, limited to the most recent 50 messages to prevent excessive storage growth, with proper attribution of message sources.

## Storage Architecture

The Mission Assistant leverages the Semantic Workbench Assistant library's storage capabilities to maintain mission state and artifacts. The storage architecture is structured as follows:

```
missions/
├── mission_id_1/
│   ├── hq/                 # HQ conversation data
│   │   └── conversation_role.json  # HQ role information
│   ├── field_conv_id_1/    # Field conversation 1 data
│   │   └── conversation_role.json  # Field role information
│   ├── field_conv_id_2/    # Field conversation 2 data
│   │   └── conversation_role.json  # Field role information
│   └── shared/             # Shared artifacts
│       ├── mission_briefing/        # Mission briefing artifacts
│       │   └── briefing.json        # Mission briefing data
│       ├── mission_kb/              # Knowledge base content
│       │   └── kb.json              # Knowledge base sections
│       ├── mission_status/          # Mission status information
│       │   └── status.json          # Current mission status
│       ├── field_request/           # Field requests
│       │   ├── request_id_1.json    # Individual request files
│       │   └── request_id_2.json    # Each with a unique UUID
│       ├── mission_log/             # Mission event log
│       │   └── log.json             # Chronological event log
│       └── hq_conversation/         # HQ conversation storage
│           └── hq_conversation.json # Recent HQ messages for field access
└── mission_id_2/
    └── ...
```

Key implementation details:
- Using the assistant library's `storage_directory_for_context()` to generate unique storage paths
- Storing Pydantic models via the library's `read_model()` and `write_model()` functions
- Each mission gets a unique folder with subfolders for each participant conversation
- Role information stored in conversation-specific directories
- Shared folder contains artifacts accessible across all conversations in the mission
- Field requests stored as individual files with UUID-based filenames
- HQ conversation messages stored in a centralized JSON file for field access
- Mission log maintained as a single growing JSON file with chronological entries
- Clean separation between conversation-specific and shared mission data

## Role-Based Behavior

The mission assistant provides a customized experience based on whether the user is in HQ or Field mode:

### HQ Role (Definition Stage)

- Creates and updates the Mission Briefing with goals and success criteria
- Develops and refines the Mission KB with mission-critical information
- Shares the Mission ID directly with Field personnel for easy access
- Has control over what information is included in the Mission KB
- Receives and resolves Field Requests from field agents
- Sees all active requests from all field agents with their priorities
- Controls the "Ready for Field" gate transition
- Receives notifications when field agents delete their requests
- Gets comprehensive mission data directly in the LLM prompt context

### Field Role (Working Stage)

- Works with the Mission KB provided by HQ
- Creates Field Requests when encountering information gaps or blockers
- Deletes Field Requests that are no longer needed
- Joins missions directly using the mission ID
- Views requests from other field agents in read-only mode
- Reports on progress and findings
- Updates Mission Status with completed tasks
- Marks individual success criteria as completed
- Views recent HQ conversations for context
- Gets comprehensive mission data directly in the LLM prompt context

## Data Models

Five key entity types provide the foundation for mission communication:

1. **Mission Briefing**:
   - Mission name and description
   - Goals with priority levels
   - Success criteria with completion tracking
   - Individual criterion completion with timestamp and attribution
   - Version tracking for modifications

2. **Mission KB**:
   - Structured sections with titles and content
   - Tagging system for organization
   - Version tracking for updates
   - Order-based section arrangement
   - Content formatting with Markdown support

3. **Mission Status**:
   - Overall progress percentage tracking (0-100%)
   - Current state (planning, ready_for_field, in_progress, completed, aborted)
   - Next actions and blockers
   - Success criteria count tracking
   - Lifecycle metadata for gate transitions
   - Attribution of state changes

4. **Field Requests**:
   - Prioritized information needs (low, medium, high, critical)
   - Status tracking (new, acknowledged, in_progress, resolved, deferred)
   - Complete request lifecycle (creation, deletion)
   - UUID-based identification with flexible matching
   - Resolution information and update history
   - Conversation-based ownership controls

5. **Mission Log**:
   - Chronological record of all events
   - Rich categorization system with specialized entry types
   - Attribution of actions to specific users
   - Metadata for event context
   - Events for gate transitions, request handling, and KB updates
   - Request deletion tracking

6. **HQ Conversation Storage**:
   - Shared access to HQ conversation for field agents
   - Content and sender metadata preservation
   - Limited message history with automatic pruning
   - Read-only access for field agents
