# Knowledge Transfer Assistant Refactoring Plan

## Overview

This document outlines a comprehensive refactoring plan to migrate remaining project assistant artifacts to be more aligned with the Knowledge Transfer Assistant's specific Jobs to be Done (JTBD). The goal is to transform project management concepts into knowledge transfer concepts that support three primary user roles:

1. **Producer** (Coordinator): Offload knowledge from their head/docs into a system to share
2. **Learner** (Team member): Go from unfamiliar to well-informed without needing a human tutor
3. **Explorer** (Team member): Gain clarity and insights by exploring a defined knowledge space

## Conceptual Mappings

Before diving into specific refactors, here are the key conceptual mappings from project management to knowledge transfer:

| Project Concept | Knowledge Transfer Concept | Rationale |
|----------------|---------------------------|-----------|
| Project | Knowledge Package | A bundle of related knowledge to be transferred |
| Project Brief | Knowledge Brief | Context, scope, and learning objectives for the knowledge |
| Project Goals | Learning Objectives | What learners should understand or be able to do |
| Success Criteria | Learning Outcomes | Specific, measurable indicators of knowledge acquisition |
| Project State | Transfer State | Stage in the knowledge transfer lifecycle |
| Project Whiteboard | Knowledge Digest | Auto-curated FAQ and key information summary |

## High Priority Refactors

### 1. Data Models (`assistant/data.py`) - **CRITICAL**

**Current State**: Heavy project management focus with ProjectState, ProjectGoal, ProjectBrief, etc.

**Proposed Refactor**:

```python
# Replace ProjectState with KnowledgeTransferState
class KnowledgeTransferState(str, Enum):
    ORGANIZING = "organizing"      # Producer is capturing and organizing knowledge
    READY_FOR_TRANSFER = "ready_for_transfer"  # Knowledge is ready for consumers
    ACTIVE_TRANSFER = "active_transfer"        # Consumers are actively learning/exploring
    COMPLETED = "completed"        # Transfer objectives achieved
    ARCHIVED = "archived"         # Knowledge package archived

# Replace ProjectGoal with LearningObjective
class LearningObjective(BaseModel):
    id: str
    title: str                    # What learners should understand
    description: str              # Detailed explanation of the objective
    priority: int = 1
    learning_outcomes: List[LearningOutcome] = Field(default_factory=list)

# Replace SuccessCriterion with LearningOutcome
class LearningOutcome(BaseModel):
    id: str
    description: str              # Specific, measurable outcome
    achieved: bool = False        # Whether this outcome has been achieved
    achieved_at: Optional[datetime] = None
    achieved_by: Optional[str] = None

# Replace ProjectInfo with KnowledgePackageInfo
class KnowledgePackageInfo(BaseModel):
    share_id: str               # Unique identifier for the knowledge package
    transfer_state: KnowledgeTransferState = KnowledgeTransferState.ORGANIZING
    coordinator_conversation_id: Optional[str] = None    # ID of the coordinator's conversation
    team_conversation_id: Optional[str] = None    # ID of the team conversation
    share_url: Optional[str] = None           # Shareable URL for inviting team members
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    updated_by: Optional[str] = None          # User ID who last updated the package
    transfer_notes: Optional[str] = None      # Notes about the transfer progress
    completion_percentage: Optional[int] = None       # Learning progress percentage (0-100)
    next_learning_actions: List[str] = Field(default_factory=list)  # Suggested next steps for learners
    version: int = 1              # Version counter for tracking changes
    achieved_outcomes: int = 0    # Count of achieved learning outcomes
    total_outcomes: int = 0       # Total count of learning outcomes
    transfer_lifecycle: Dict[str, Any] = Field(default_factory=dict)  # Transfer metadata

# Replace ProjectBrief with KnowledgeBrief
class KnowledgeBrief(BaseEntity):
    title: str                    # Name of the knowledge package
    description: str              # Comprehensive context and scope
    learning_objectives: List[str] = Field(default_factory=list)  # What consumers will learn
    target_audience: Optional[str] = None     # Who this knowledge is for
    prerequisites: Optional[str] = None       # What learners should know beforehand
    additional_context: Optional[str] = None  # Supplementary information

# Replace ProjectWhiteboard with KnowledgeDigest
class KnowledgeDigest(BaseEntity):
    content: str = ""             # Auto-curated knowledge summary (FAQ format)
    is_auto_generated: bool = True # Whether content was auto-generated or manually edited

# Keep InformationRequest as-is for now

# Update LogEntryType for knowledge transfer events
class LogEntryType(str, Enum):
    KNOWLEDGE_BRIEF_CREATED = "knowledge_brief_created"
    KNOWLEDGE_BRIEF_UPDATED = "knowledge_brief_updated"
    LEARNING_OBJECTIVE_ADDED = "learning_objective_added"
    LEARNING_OUTCOME_ACHIEVED = "learning_outcome_achieved"
    # Keep existing information request events as-is
    TRANSFER_STATE_CHANGED = "transfer_state_changed"
    # Keep existing participant events as-is
    KNOWLEDGE_TRANSFER_STARTED = "knowledge_transfer_started"
    KNOWLEDGE_TRANSFER_COMPLETED = "knowledge_transfer_completed"
    KNOWLEDGE_ARCHIVED = "knowledge_archived"
    KNOWLEDGE_UPDATE = "knowledge_update"
    # ... additional knowledge-focused events

# Replace Project with KnowledgePackage
class KnowledgePackage(BaseModel):
    """
    A comprehensive representation of a knowledge package, including its brief, repository,
    knowledge gap requests, logs, and other related entities.

    This model encapsulates all the components that make up a knowledge transfer package,
    providing a single point of access to all relevant information for Coordinators and Team members.
    It serves as the main interface for interacting with the knowledge transfer data.
    """

    info: Optional[KnowledgePackageInfo]
    brief: Optional[KnowledgeBrief]
    learning_objectives: List[LearningObjective] = Field(default_factory=list)
    requests: List[InformationRequest] = Field(default_factory=list)
    digest: Optional[KnowledgeDigest]
    log: Optional[TransferLog] = Field(default_factory=lambda: TransferLog())

# Also rename ProjectLog to TransferLog
class TransferLog(BaseModel):
    """
    A chronological record of all actions and interactions during knowledge transfer,
    including updates and learning progress reports.
    """
    entries: List[LogEntry] = Field(default_factory=list)
```

### 2. Command System (`assistant/command_processor.py`) - **HIGH**

**Current State**: Commands focused on project management (`/create-brief`, `/add-goal`, etc.)

**Proposed Refactor**:

**Coordinator Commands**:

- `/create-brief` → `/create-knowledge-brief` (rename existing)
- `/add-goal` → `/add-learning-objective` (rename existing)
- `/resolve-request` → Keep as-is (information request terminology works fine)

**Team Commands**:

- `/request-info` → Keep as-is (requesting information works fine)
- `/update-status` → Keep as-is (status updates are still relevant)
- `/sync-files` → Keep as-is (file sync functionality unchanged)

**Shared Commands**:

- `/project-info` → `/knowledge-info` (rename existing)
- `/list-participants` → Keep as-is (participants terminology works fine)

### 3. Configuration (`assistant/config.py`) - **MEDIUM**

**Current State**: Mixed project and knowledge transfer terminology

**Proposed Refactor**:

- Update prompt configuration field names to use "knowledge" instead of "project"
- Update welcome messages to emphasize knowledge transfer value proposition
- Rename configuration sections to align with knowledge transfer roles
- Update default messages to focus on learning and exploration rather than task execution

### 4. Storage Models (`assistant/storage_models.py`) - **MEDIUM**

**Current State**: Project-centric storage concepts

**Proposed Refactor**:

```python
# Keep ConversationRole as COORDINATOR/TEAM for now
class ConversationRole(str, Enum):
    COORDINATOR = "coordinator"
    TEAM = "team"

class CoordinatorConversationMessage(BaseModel):
    """Model for storing messages from Coordinator conversation for Team access."""
    # ... same structure but renamed for clarity

class CoordinatorConversationStorage(BaseModel):
    """Model for storing Coordinator conversation messages."""
    knowledge_share_id: str  # Renamed from project_id
    # ... rest of structure
```

### 5. Manager Classes (`assistant/manager.py`) - **HIGH**

**Current State**: ProjectManager class with project-focused methods

**Proposed Refactor**:

- Rename `ProjectManager` to `KnowledgeTransferManager`
- Update method names:
  - `create_project_brief` → `create_knowledge_brief`
  - `add_project_goal` → `add_learning_objective`
  - `get_project_info` → `get_knowledge_package_info`
  - `update_project_state` → `update_transfer_state`
- Update internal logic to use knowledge transfer concepts
- Modify state transitions to align with knowledge transfer lifecycle

### 6. File Organization and Naming - **LOW**

**Current State**: Many files use "project" in names or internal references

**Proposed Refactor**:

- Consider renaming core files to use "knowledge" terminology where appropriate
- Update internal variable names from "project_*" to "knowledge_*" or "transfer_*"
- Update function and class names to align with knowledge transfer domain

## Medium Priority Refactors

### 7. Text Includes Cleanup (`assistant/text_includes/`) - **MEDIUM**

**Current State**: Text includes are already properly aligned with knowledge transfer

**Proposed Actions**:

- **Verify remaining files** use consistent knowledge transfer terminology
- **No major changes needed** - files already focus on knowledge transfer concepts

### 8. State Inspector (`assistant/state_inspector.py`) - **MEDIUM**

**Current State**: Likely uses project terminology in dashboard

**Proposed Refactor**:

- Update dashboard labels and metrics to focus on knowledge transfer progress
- Show learning objectives progress instead of project goals
- Display knowledge gaps instead of project blockers
- Rename dashboard sections to align with knowledge transfer concepts

### 9. Tools (`assistant/tools.py`) - **MEDIUM**

**Current State**: Tool functions likely use project terminology

**Proposed Refactor**:

- Rename LLM tool functions to use knowledge transfer concepts
- Update tool descriptions and prompts to focus on knowledge transfer actions
- Ensure tools support the Producer/Learner/Explorer workflow

## Low Priority Refactors

### 10. Notifications (`assistant/notifications.py`) - **LOW**

**Current State**: Notification messages likely use project language

**Proposed Refactor**:

- Update notification messages to use knowledge transfer terminology
- Ensure notifications emphasize learning and knowledge exploration

### 11. Documentation Updates - **LOW**

**Current State**: Various documentation may still reference project concepts

**Proposed Actions**:

- Update `README.md` to focus on knowledge transfer use cases
- Update `CLAUDE.md` to emphasize knowledge transfer architecture
- Update any other documentation to align with JTBD

### 12. Test Updates (`tests/`) - **LOW**

**Current State**: Tests likely use project terminology and concepts

**Proposed Actions**:

- Update test names and assertions to use knowledge transfer concepts
- Ensure tests validate knowledge transfer workflows rather than project management
- Update mock data to reflect knowledge transfer scenarios

## Implementation Strategy

### Phase 1: Core Data Models (High Impact)

1. Refactor `data.py` with new knowledge transfer models
2. Update `manager.py` to use new models
3. Update storage integration points

### Phase 2: User Interface (High Visibility)

1. Refactor command system in `command_processor.py`
2. Update configuration in `config.py`
3. Clean up text includes

### Phase 3: Supporting Systems (Medium Impact)

1. Update state inspector and tools
2. Refactor storage models
3. Update notifications

### Phase 4: Polish and Documentation (Low Risk)

1. File naming and organization
2. Documentation updates
3. Test updates

## Success Criteria

The refactoring will be considered successful when:

1. **Terminology Alignment**: All user-facing language consistently uses knowledge transfer concepts
2. **Workflow Support**: Commands and interfaces clearly support Producer, Learner, and Explorer workflows
3. **Conceptual Clarity**: The system clearly focuses on knowledge transfer rather than task/project execution
4. **JTBD Alignment**: Features directly support the three knowledge transfer jobs (Offload, Learn, Explore)
5. **Reduced Confusion**: No mixing of project management and knowledge transfer concepts

## Risk Mitigation

- **Breaking Changes**: Implement database migration strategies for existing data
- **User Confusion**: Provide clear communication about terminology changes
- **Feature Gaps**: Ensure all current functionality is preserved under new terminology
- **Testing**: Comprehensive testing of refactored components before deployment

This refactoring plan will transform the assistant from a generic project management tool into a focused, purpose-built knowledge transfer system that directly supports the identified JTBD for Producers, Learners, and Explorers.
