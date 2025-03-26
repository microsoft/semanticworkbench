# Mission Assistant Implementation Plan

## Overview

The Mission Assistant is designed as a dual-mode context transfer system that facilitates knowledge transfer between different conversations in the Semantic Workbench. It provides a structured way for HQ to create mission information and Field personnel to access it, with bidirectional updates and communication.

## System Design

The Mission Assistant is built as a dual-mode context transfer assistant:

1. **HQ Mode (Definition Stage)**:
   - Mission Briefing Creation: HQ articulates the mission goals and success criteria
   - Knowledge Base Development: Collection and organization of mission-critical information
   - Mission Preparation: Ensuring the Knowledge Base is complete and ready for field use
   - Gate: "Ready for Field" checkpoint ensures mission information meets quality criteria

2. **Field Mode (Working Stage)**:
   - Field Operations: Field personnel interact with the Mission KB to accomplish goals
   - Request Logging: Unresolved questions or information gaps are automatically logged
   - HQ Support: HQ is notified of Field Requests and resolves them asynchronously
   - Gate: "Mission Completion" checkpoint indicates all success criteria have been met

The system supports an iterative and asynchronous workflow where the Field's operations and the HQ's support activities can occur concurrently, with a dynamic information radiator to display the current mission status.

## Artifacts and State

The Mission Assistant manages several key artifacts:

1. **Mission Briefing**: A clear, concise statement of the mission, including goals, success criteria, and high-level context necessary for the Field to start. Owned by HQ.

2. **Mission KB (Knowledge Base)**: The curated information necessary for the Field to carry out the mission, kept up-to-date by HQ with clear logs of updates. Owned by HQ, made accessible to the Field.

3. **Mission Status**: A dynamic representation of progress toward success, updated in real time to reflect remaining tasks, active Field Requests, and Field reports. Visible to both HQ and Field in the information radiator.

4. **Field Requests**: A concise, prioritized list of Field needs—specifically unresolved blockers, missing information, or required resources—logged for HQ review and resolution. Logged by the Field assistant, managed for review by HQ.

5. **Mission Log**: A chronological record of all actions and interactions during the mission, including updates to the Mission KB, resolutions of Field Requests, and progress reports from the Field. Maintained by the system, visible to both HQ and Field.

## Storage Architecture

The Mission Assistant will leverage the Semantic Workbench Assistant library's storage capabilities to maintain mission state and artifacts. The storage architecture will be structured as follows:

```
missions/
├── mission_id_1/
│   ├── hq/                 # HQ conversation data
│   ├── field_conv_id_1/    # Field conversation 1 data
│   ├── field_conv_id_2/    # Field conversation 2 data
│   └── shared/             # Shared artifacts
│       ├── briefing/       # Mission briefing artifacts
│       ├── kb/             # Knowledge base content
│       ├── requests/       # Field requests
│       └── log/            # Mission event log
└── mission_id_2/
    └── ...
```

Key implementation details:
- Using the assistant library's `storage_directory_for_context()` to generate unique storage paths
- Storing Pydantic models via the library's `read_model()` and `write_model()` functions
- Maintaining derivative representations of conversations rather than duplicating the full conversation content
- Each mission gets a unique folder with subfolders for each participant conversation
- Shared folder contains artifacts accessible across all conversations in the mission

## Role-Based Behavior

The mission assistant provides a customized experience based on whether the user is in HQ or Field mode:

### HQ Role (Definition Stage)

- Creates and updates the Mission Briefing with goals and success criteria
- Develops and refines the Mission KB with mission-critical information
- Initiates missions by sending invitations to Field personnel
- Has control over what information is included in the Mission KB
- Receives notifications when invitations are accepted
- Receives Field Requests and resolves them
- Can view all users participating in the mission
- Can revoke access to the mission
- Controls the "Ready for Field" gate

### Field Role (Working Stage)

- Works with the Mission KB provided by HQ
- Logs Field Requests when encountering information gaps
- Receives and accepts mission invitations
- Reports on progress and findings
- Updates Mission Status with completed tasks
- Sees real-time updates to the Mission KB
- Has mission-specific commands for operational tasks

## Artifact Data Models

Five key artifact types provide the foundation for mission communication:

1. **Mission Briefing**:
   - Mission name and description
   - Goals with priority levels
   - Success criteria with completion tracking

2. **Mission KB**:
   - Structured sections with titles and content
   - Tagging system for organization
   - Version tracking for updates

3. **Mission Status**:
   - Overall progress tracking
   - Current state (planning, in_progress, etc.)
   - Next actions and blockers

4. **Field Requests**:
   - Prioritized information needs
   - Status tracking (new, acknowledged, resolved)
   - Resolution information and history

5. **Mission Log**:
   - Chronological record of all events
   - Categorized entry types
   - Links to related artifacts
