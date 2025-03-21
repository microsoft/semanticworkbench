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

## Technical Architecture

### Cross-Conversation Communication

We leverage Semantic Workbench's existing capabilities to enable cross-conversation communication:

1. **State Management**: 
   - Each conversation has its own storage directory
   - `MissionStateManager` stores conversation links and state information
   - Pydantic models define the structure of linked conversation data

2. **Message-Based Artifact Sharing**:
   - Message metadata carries structured artifact data between conversations
   - `ArtifactMessenger` handles serialization, sending, and receiving
   - Local storage maintains artifacts with version tracking
   - Conflict detection and resolution for concurrent updates

3. **Conversation Access**:
   - `ConversationClientManager` creates API clients for cross-conversation operations
   - Each client maintains proper authentication context
   - Temporary contexts enable using context methods on remote conversations

4. **Role Detection**:
   - Detect whether a conversation is in HQ or Field Mode based on artifacts
   - Store role in conversation metadata
   - Adjust assistant behavior based on detected role

### Invitation System

The invitation system establishes secure links between conversations:

1. **Invitation Creation**:
   - HQ Mode creates secure invitation tokens
   - Links are stored in the Workbench sharing system
   - Invitation metadata includes mission-specific information

2. **Invitation Acceptance**:
   - Field Mode joins using invitation tokens
   - Establishes bidirectional conversation links
   - Role assignment based on invitation flow

3. **Bidirectional Communication**:
   - Both sides maintain links to each other
   - Updates flow in both directions
   - Each conversation knows its role in the mission

### Artifact Data Models

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

## Implementation Plan

### Phase 1: Core Functionality (Completed)

1. **Cross-Conversation Communication**
   - ✅ Implement structured message exchange between linked conversations
   - ✅ Develop artifact data models for serialization/deserialization
   - ✅ Create handlers for processing artifact update messages

2. **Invitation Flow**
   - ✅ Create a secure invitation creation and validation system
   - ✅ Integrate with the existing conversation sharing API
   - ✅ Implement the `/invite` and `/join` commands
   - ✅ Add notifications when invitations are accepted
   - ✅ Establish bidirectional communication channels

3. **Artifact Management**
   - ✅ Create data models for the five key artifacts
   - ✅ Implement serialization/deserialization with version tracking
   - ✅ Add command handlers for creating and updating artifacts
   - ✅ Create the information display system (`/mission-info`)

4. **Role-Based Behavior**
   - ✅ Detect user role (HQ vs. Field) in each conversation
   - ✅ Customize assistant messages based on user role
   - ✅ Offer different command sets for HQ and Field

### Phase 2: Lifecycle Stages and Information Intelligence (In Progress)

1. **Improve Field Request System**
   - ✅ Add `/resolve-request` command for HQ to mark requests as resolved
   - ✅ Implement request notification to HQ
   - ✅ Add request resolution tracking and history

2. **Implement Lifecycle Stages and Gates**
   - ✅ Create state tracking for HQ and Field stages
   - ✅ Implement the "Ready for Field" gate mechanism
   - ✅ Implement the "Mission Completion" gate mechanism
   - ✅ Add stage transition commands and notifications

3. **Enhance Information Radiator**
   - ✅ Improve mission-info display with real-time updates
   - ✅ Add customized views based on user role
   - Add progress visualizations and summaries

4. **Add Tool-Driven Intelligence**
   - ✅ Create tool functions for mission assistant
   - ✅ Implement proactive field request detection
   - ✅ Add automated lifecycle stage management
   - ✅ Create progress tracking tools

### Phase 3: User Experience Improvements (Planned)

1. **Add Feedback and Status Messages**
   - Show KB update notifications
   - Provide clear error messages for communication failures
   - Add status indicators for mission progress

2. **Improve Command Handling**
   - Add command autocompletion suggestions
   - Provide contextual help based on user actions
   - Implement natural language command detection

3. **Error Handling Improvements**
   - Handle failures in message delivery
   - Implement retry mechanisms
   - Provide clear error messages to users

### Phase 4: Security and Mission Control (Planned)

1. **Implement Advanced Security**
   - Only allow artifact sharing between conversations with proper permissions
   - Verify user identity for sensitive operations
   - Add confirmation steps for critical actions

2. **Add Mission Control Features**
   - Configure visibility of KB sections
   - Set access permissions to mission artifacts
   - Add mission abort and emergency protocols
   - Control access to sensitive mission information

## Testing Plan

1. **Unit Testing**
   - Test artifact model serialization/deserialization
   - Test invitation creation and validation
   - Test message construction and parsing
   - Test role detection and command permissions

2. **Integration Testing**
   - Test cross-conversation message passing
   - Test invitation and acceptance between two conversations
   - Test artifact sharing between linked conversations
   - Test role-based behavior differences

3. **Failure Testing**
   - Test handling of message delivery failures
   - Test invitation expiration/rejection
   - Test recovery from error states
   - Test handling of conflicting artifact updates

## Status and Next Steps

### Current Status
We have implemented the core functionality of the Mission Assistant, including:
- Message-based artifact sharing between conversations
- Five key artifact types with serialization/deserialization
- Invitation system for linking conversations
- Role-specific commands and behavior
- Information radiator via `/mission-info`
- Tool-driven assistant intelligence with proactive field request detection
- Mission lifecycle tracking with gate transitions

### Implementation Updates
1. ✅ Fixed linting and type checking issues across all modules
2. ✅ Resolved circular dependencies using dynamic imports
3. ✅ Added proper type annotations to address Optional parameters
4. ✅ Added lifecycle attribute to MissionStatus for gate tracking
5. ✅ Created pyrightconfig.json to manage type checking strictness
6. ✅ Added basic test framework for tool functionality testing
7. ✅ Fixed ConversationMessage constructor calls in mission_tools.py

### Immediate Next Steps
1. ✅ Implement `/resolve-request` command for HQ to resolve Field Requests
2. ✅ Add lifecycle stage tracking and gate transitions
3. ✅ Add proactive Field Request detection through tool functions
4. ✅ Implement tool-driven assistant intelligence
5. Address remaining type checking issues (currently suppressed)
6. Add UI/visualizations for the information radiator
7. Test with two separate conversations in HQ/Field roles
8. Add multi-participant role management

### Long-Term Roadmap
1. Integrate with other MCP servers for enhanced capabilities
2. Add support for multi-participant conversations in both roles
3. Create a graphical UI component for the information radiator
4. Implement analytics for mission performance tracking
5. Add templates for common mission types