# Semantic Workbench State Management

This document provides an overview of the state management facilities available in the Semantic Workbench ecosystem that can be leveraged by assistants.

## Architectural Overview

```mermaid
graph TD
    subgraph "Workbench Service"
        DB[(SQL Database)]
        FileStore[(File Storage)]
        API[API Endpoints]
        Events[Event System]
    end

    subgraph "Assistant Instance"
        AState[Assistant State API]
        AStorage[Storage Directory]
        EventHandler[Event Handler]
    end

    subgraph "Conversation"
        Messages[Messages]
        Metadata[Message Metadata]
        ConvFiles[Conversation Files]
    end

    API <--> AState
    API <--> Messages
    API <--> ConvFiles
    API <--> Metadata
    FileStore <--> ConvFiles
    DB <--> Messages
    DB <--> Metadata
    Events ---> EventHandler
    EventHandler ---> AState
    AState ---> AStorage

    classDef persistent fill:#b7e1cd,stroke:#82c3a6
    classDef transient fill:#f8cecc,stroke:#b85450
    classDef storage fill:#d5e8d4,stroke:#82b366

    class DB,FileStore,AStorage persistent
    class Events transient
    class ConvFiles,AState storage
```

## State Storage Locations

```mermaid
graph LR
    subgraph "Persistent Storage"
        DB[(SQL Database<br>PostgreSQL/SQLite)]
        FileStore[(File Storage<br>Binary Files)]
        LocalFS[(Local Filesystem<br>JSON Files)]
    end
    
    subgraph "State Types"
        Messages[Messages]
        MsgMeta[Message Metadata]
        ConvFiles[Conversation Files]
        AssistState[Assistant State API]
        PrivateState[Private Assistant Data]
    end
    
    Messages --> DB
    MsgMeta --> DB
    ConvFiles --> FileStore
    AssistState --> DB
    PrivateState --> LocalFS
    
    classDef db fill:#dae8fc,stroke:#6c8ebf
    classDef file fill:#d5e8d4,stroke:#82b366
    classDef local fill:#ffe6cc,stroke:#d79b00
    
    class DB db
    class FileStore file
    class LocalFS local
```

## Conversation-level State Management

### Message Metadata

- **Key Mechanism**: Each message can include arbitrary metadata as JSON
- **Storage**: Persisted in the database with the message
- **Special Fields**:
  - `attribution`: Source information displayed after the sender
  - `href`: Makes message a hyperlink
  - `debug`: Debug information accessible through UI inspection
  - `footer_items`: Additional information displayed in the message footer
  - `tool_calls`: Structured representation of tool invocations
  - `tool_result`: Results from tool executions
- **Usage**: Primary method for assistants to store structured data
- **Limitations**: Cannot be used to transfer large amounts of data (practical limit around 100KB)

### Files/Attachments

- **Model**: Files are represented as `File` and `FileVersion` entities in the database
- **Storage**: Files are stored in a filesystem-based storage system managed by the Workbench service
- **Versioning**:
  - Built-in version tracking for files with the same name
  - All files with the same name in a conversation are treated as versions of the same file
  - No way for users to explicitly designate a file with the same name as a new file rather than a new version
- **Access**:
  - Files are visible in the conversation UI for users
  - Files can be attached to messages via the `filenames` property
  - Files can be uploaded, downloaded, and deleted through the UI
- **Permissions**: Files inherit conversation permissions
- **Limitations**:
  - No direct UI for viewing or managing different versions of a file
  - No way for users to specify storage at the assistant level versus conversation level

### Conversation Sharing

- **Usage**: Enables controlled access to conversation content
- **Details**: See SHARING.md for comprehensive details on the sharing mechanism

### Events System

- **Purpose**: Propagates changes to all conversation participants
- **Model**: `ConversationEvent` defines various event types
- **Types**: Message created/deleted, participant changes, etc.
- **Delivery**: Events delivered through Server-Sent Events (SSE)
- **Storage**: Events are not stored persistently - they are transient objects
- **Connection Requirements**: Recipients must be actively connected to receive events
- **Durability**: No event replay mechanism - events missed during disconnection are lost permanently
- **Limitations**: Cannot be relied upon for critical state synchronization due to potential message loss

```mermaid
sequenceDiagram
    participant User as User
    participant Assistant as Assistant
    participant API as Workbench API
    participant Events as Event System
    participant DB as Database
    
    Note over User,DB: Both connected
    
    User->>API: Send message
    API->>DB: Store message
    API->>Events: Generate message_created event
    Events->>User: Notify via SSE
    Events->>Assistant: Notify via SSE
    
    Note over User,DB: Assistant disconnects
    
    User->>API: Edit message
    API->>DB: Update message
    API->>Events: Generate message_updated event
    Events->>User: Notify via SSE
    Events--xAssistant: Event lost (disconnected)
    
    Note over User,DB: Assistant reconnects
    
    Assistant->>API: Get conversation
    API->>DB: Query messages
    API->>Assistant: Return current state
    
    Note over User,DB: No automatic notification<br/>about missed events
```

## Assistant-level State Management

### Assistant State API

- **Type**: Server-side state managed by the Workbench service
- **Model**: Assistants maintain state via `StateResponseModel` in the database
- **Structure**: Structured data represented as JSON schema
- **UI Integration**: UI schema maintained for display formatting in Workbench UI
- **Description**: State descriptions provide user-facing information
- **Persistence**: State persisted in the central SQL database (PostgreSQL/SQLite)
- **Access**: Accessible via REST API endpoints in the Workbench service
- **Visibility**: Can be exposed to users through UI integrations

### Assistant Storage Directory

- **Type**: Local filesystem storage specific to each assistant instance
- **Purpose**: Private storage for assistant-specific data
- **Location**: Typically `.data/assistants/[assistant-id]` directory
- **Implementation**: Created and managed by `storage.py` in semantic-workbench-assistant
- **Content**: Pydantic models serialized to JSON files via `write_model` function
- **Visibility**: Not exposed to users through the UI
- **Usage**: Appropriate for:
  - Private cross-conversation data
  - Assistant-specific configuration
  - Cached or derived data
  - Data that doesn't need UI visibility

### Configuration

- **Storage**: Assistant configuration stored in metadata
- **Scope**: Configuration specific to each assistant instance
- **Access**: Available through assistant service APIs

## Cross-conversation Communication

### Cross-Conversation Access

- Allows assistants to interact with multiple conversations simultaneously
- Requires proper permissions and active participant records
- Managed through the conversation sharing system
- See SHARING.md for comprehensive details on:
  - Permission models and enforcement
  - User vs. assistant access patterns
  - Conversation sharing mechanisms
  - Principal and participant relationships

### File Transfer

- **Mechanism**: Files must be explicitly copied between conversations
- **Process**:
  1. Read file content from source conversation
  2. Create new file with same name in target conversation
  3. This creates a completely separate file, not linked to the original
- **Versioning**: Version history doesn't transfer between conversations

```mermaid
sequenceDiagram
    participant ConvA as Conversation A
    participant API as Workbench API
    participant ConvB as Conversation B
    participant FSA as File Storage A
    participant FSB as File Storage B
    
    Note over ConvA,FSB: File Transfer Process
    
    ConvA->>API: Request file content<br/>(conversation_id_A, filename)
    API->>FSA: Retrieve file content
    FSA->>API: Return file content
    API->>ConvA: File content
    
    ConvA->>API: Upload to conversation B<br/>(conversation_id_B, filename, content)
    API->>FSB: Store file content
    API->>ConvB: Create file record
    
    Note over ConvA,FSB: Result: Two independent files with<br/>same name but separate version history
```

### Participant Model

- **Types**: User participants and assistant participants
- **Status**: Online/offline status tracking
- **Permissions**: Read/write access controls
- **Events**: Participant join/leave events

## File Storage Architecture

### Storage System

- **Physical Storage**: Files stored in filesystem managed by Workbench service
- **Reference System**: Messages and conversations reference files by name
- **Uniqueness**: Files are uniquely identified by the combination of conversation ID and filename
- **UI Integration**: Only conversation-level files are shown in the UI

```mermaid
graph TD
    subgraph "File Management System"
        FileDB[(File Database)]
        FileStore[(Physical File Storage)]
    end
    
    subgraph "Conversation 1"
        Conv1[Conversation ID: 1]
        File1A["File: report.pdf (v1)"]
        File1B["File: report.pdf (v2)"]
        Conv1 --- File1A
        Conv1 --- File1B
    end
    
    subgraph "Conversation 2"
        Conv2[Conversation ID: 2]
        File2["File: report.pdf (v1)"]
        Conv2 --- File2
    end
    
    subgraph "Message References"
        Msg1["Message 1: with filenames=['report.pdf']"]
        Msg2["Message 2: with filenames=['report.pdf']"]
    end
    
    File1A -- "Version 1" --> FileStore
    File1B -- "Version 2" --> FileStore
    File2 -- "Version 1" --> FileStore
    
    File1A --> FileDB
    File1B --> FileDB
    File2 --> FileDB
    
    Msg1 -. "References latest version (v2)" .-> File1B
    Msg2 -. "References latest version (v1)" .-> File2
    
    classDef conversation fill:#f9f,stroke:#333,stroke-width:2px
    classDef file fill:#bbf,stroke:#333
    classDef storage fill:#bfb,stroke:#333
    classDef message fill:#fbb,stroke:#333
    
    class Conv1,Conv2 conversation
    class File1A,File1B,File2 file
    class FileDB,FileStore storage
    class Msg1,Msg2 message
```

### File Versioning

- **Automatic Versioning**: When a file with the same name is uploaded to a conversation, it's treated as a new version
- **Version Control**: The system maintains version numbers and history
- **Access Control**: API allows requesting specific versions or defaulting to latest
- **Conflict Management**: No built-in conflict resolution for simultaneous updates

```mermaid
sequenceDiagram
    participant User1 as User 1
    participant Conv as Conversation
    participant DB as Database
    participant FS as File Storage
    
    User1->>Conv: Upload "report.pdf" (v1)
    Conv->>DB: Create file record<br/>conversation_id: 123<br/>filename: "report.pdf"<br/>version: 1
    Conv->>FS: Store file content with<br/>hash-based path
    
    Note over User1,FS: Later...
    
    User1->>Conv: Upload new "report.pdf"
    Conv->>DB: Find existing file with<br/>same name in conversation
    Conv->>DB: Create new version<br/>conversation_id: 123<br/>filename: "report.pdf"<br/>version: 2
    Conv->>FS: Store new content with<br/>different hash-based path
    
    Note over User1,FS: Request file
    
    User1->>Conv: Request "report.pdf"
    Conv->>DB: Find file, get latest version (v2)
    Conv->>FS: Retrieve content for version 2
    Conv->>User1: Return file content
```

### File Naming

- **Namespace**: Filenames must be unique within a conversation
- **Constraints**: Database enforces uniqueness via constraints
- **Workaround**: To have logically different files with the same name, users must use different filenames (e.g., "report-v2.pdf")

## Data Export/Import

### Serialization

- Both conversations and assistants support export/import
- Data can be transferred between instances while maintaining relationships
- Export includes messages, files, and metadata

### Persistence

- Database uses SQLModel with async SQLAlchemy
- Supports both SQLite and PostgreSQL databases

## Access Patterns

### Direct API Calls

- Assistants can make authenticated API calls to the Workbench service
- API endpoints available for conversation, message, and file operations

### Message Commands

- Assistants can respond to commands embedded in messages
- Command responses can include structured data in metadata

### Event Subscriptions

- Assistants can subscribe to conversation events
- Real-time notifications of changes to conversations
- Requires maintaining active connections to receive events
- No guarantee of delivery - events during disconnections are lost
- Cannot be used as a reliable state synchronization mechanism

## Best Practices

### State Persistence

- Use message metadata for small conversation-specific state (<100KB)
- Use assistant state for cross-conversation persistence that needs UI integration
- Use files for larger structured data or binary content that users should see
- Use assistant storage directory for private cross-conversation data

```mermaid
graph TD
    State[State to Store]
    
    State -- "Small, conversation-specific<br/>(<100KB)" --> MessageMeta[Message Metadata]
    State -- "Shared across conversations<br/>UI integration needed" --> AssistantState[Assistant State API]
    State -- "Large data<br/>Binary content<br/>User visibility needed" --> Files[Conversation Files]
    State -- "Cross-conversation<br/>Private to assistant<br/>No UI needed" --> LocalStorage[Assistant Storage Directory]
    
    MessageMeta --> Persist[(Database)]
    AssistantState --> Persist
    Files --> FileStore[(File Storage)]
    LocalStorage --> Disk[(Local Filesystem)]
    
    classDef decision fill:#f5a9b8,stroke:#333
    classDef storage fill:#dae8fc,stroke:#6c8ebf
    classDef persist fill:#d5e8d4,stroke:#82b366
    
    class State decision
    class MessageMeta,AssistantState,Files,LocalStorage storage
    class Persist,FileStore,Disk persist
```

### Sharing Information

- Use conversation sharing for explicit permission grants
- Leverage the API for controlled cross-conversation access
- Use message metadata for lightweight information transfer
- For file sharing between conversations, implement explicit copy mechanisms

```mermaid
flowchart TD
    HQ[HQ Conversation]
    Field[Field Conversation]
    
    subgraph "Information Sharing Options"
        direction TB
        A[Message Metadata]
        B[File Transfer]
        C[Cross-conversation Messages]
        D[Assistant State]
    end
    
    HQ -- "Small data<br/>(<100KB)" --> A --> Field
    HQ -- "Large/structured data<br/>User visibility" --> B --> Field
    HQ -- "Real-time notifications" --> C --> Field
    HQ -- "Persistent shared state" --> D --> Field
    
    classDef conv fill:#f9f,stroke:#333
    classDef option fill:#bbf,stroke:#333
    
    class HQ,Field conv
    class A,B,C,D option
```

### Avoiding State Conflicts

- Establish clear ownership of data to prevent conflicting updates
- Use versioning for tracking changes over time
- Implement conflict detection and resolution for collaborative scenarios
- Use timestamps to determine the most recent updates

```mermaid
sequenceDiagram
    participant ConvA as Conversation A
    participant Central as Central State
    participant ConvB as Conversation B
    
    Note over ConvA,ConvB: State Synchronization Pattern
    
    ConvA->>Central: Read current state
    ConvA->>ConvA: Local modifications
    ConvA->>Central: Write with version check
    Central-->>ConvA: Update confirmed (v1)
    
    ConvB->>Central: Read current state (v1)
    ConvB->>ConvB: Local modifications
    
    ConvA->>Central: Read current state (v1)
    ConvA->>ConvA: More local modifications
    ConvA->>Central: Write with version check
    Central-->>ConvA: Update confirmed (v2)
    
    ConvB->>Central: Write with version check (v1)
    Central--xConvB: Conflict detected (current v2)
    ConvB->>Central: Read current state (v2)
    ConvB->>ConvB: Merge changes
    ConvB->>Central: Write with version check (v2)
    Central-->>ConvB: Update confirmed (v3)
```