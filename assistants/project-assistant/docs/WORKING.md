# Terminology Conversion Plan

## Overview
This document outlines the steps to convert "mission assistant" terminology to "project assistant" throughout the codebase.

## Progress Summary
- ✅ Python file names updated through git mv commands
- ✅ chat.py updated with new terminology throughout:
  - All imports changed to reference new file names
  - All class, role and terminology references updated
  - HQ → Coordinator, Field → Team
  - Mission → Project consistently throughout 
  - Tool references updated (create_project_brief, view_coordinator_conversation, etc.)
  - Prompts updated with new terminology
  - All function parameters updated to project-based naming
- ✅ Converting command_processor.py:
  - Updated imports and module documentation
  - Updated CommandRegistry class references to roles
  - Updated the core setup commands:
    - Renamed start-hq command to start-coordinator command
    - Updated join command for team roles
    - Updated help command with new terminology
  - Updated project configuration commands:
    - Renamed create-briefing to create-brief 
    - Updated add-goal command
    - Updated add-kb-section command
  - Updated information request commands:
    - Updated request-info command 
    - Updated update-status command
    - Updated resolve-request command
  - Updated team management commands:
    - Updated invite command
    - Updated join-legacy command
    - Updated list-participants command
    - Updated revoke-access command
  - Updated information commands:
    - Renamed mission-info to project-info and updated implementation
  - Updated command registry:
    - All command registrations updated with new terminology
    - main process_command function updated
- ✅ Converting project.py (formerly mission.py):
  - Updated module docstring
  - Updated all imports to reference new file names
  - Updated class names (MissionRoleData → ProjectRoleData)
  - Updated ConversationClientManager class references
  - Updated method names (get_hq_client_for_mission → get_coordinator_client_for_project)
  - Renamed MissionInvitation class to ProjectInvitation
  - Updated invitation methods to use project terminology
  - Updated the leave command implementation for project context
- ✅ Converting project_data.py (formerly mission_data.py):
  - Updated module docstring and overview comments
  - Updated all class docstrings with project terminology
  - Renamed all classes:
    - MissionState → ProjectState (updated enum values)
    - MissionGoal → ProjectGoal
    - MissionBriefing → ProjectBrief
    - MissionKB → ProjectKB
    - MissionStatus → ProjectDashboard
    - FieldRequest → InformationRequest
    - MissionLog → ProjectLog
  - Updated LogEntryType enums (mission_* → project_*)
  - Updated all field names and docstrings to use new terminology
  - Updated all references to roles (HQ → Coordinator, Field → Team)
- ✅ Converting project_common.py (formerly mission_common.py):
  - Updated module docstring and comments
  - Updated imports to reference new file names
  - Renamed log_mission_action to log_project_action
  - Updated all references to use new project terminology
  - Updated function arguments and docstrings
- ✅ Converting project_manager.py (formerly mission_manager.py):
  - Updated module docstring and imports
  - Updated class name (MissionManager → ProjectManager)
  - Renamed and updated all methods:
    - create_mission → create_project 
    - join_mission → join_project
    - get_mission_id → get_project_id
    - get_mission_role → get_project_role
    - get_mission_briefing → get_project_brief
    - create_mission_briefing → create_project_brief
    - update_mission_briefing → update_project_brief
    - get_mission_status → get_project_dashboard
    - update_mission_status → update_project_dashboard
    - get_field_requests → get_information_requests
    - create_field_request → create_information_request
    - update_field_request → update_information_request
    - resolve_field_request → resolve_information_request
    - get_mission_log → get_project_log
    - add_log_entry (updated references inside)
    - get_mission_kb → get_project_kb
    - add_kb_section (updated references inside)
    - update_kb_section (updated references inside)
    - complete_mission → complete_project
- ✅ Converting coordinator_mode.py (formerly hq_mode.py):
  - Updated module docstring and imports
  - Updated class name (HQConversationHandler → CoordinatorConversationHandler)
  - Renamed and updated all methods:
    - initialize_mission → initialize_project
    - create_mission_briefing → create_project_brief
    - add_mission_goal → add_project_goal
    - add_kb_section (updated references inside)
    - resolve_field_request → resolve_information_request
    - mark_mission_ready_for_field → mark_project_ready_for_working
    - get_mission_info → get_project_info
    - log_action (updated to use log_project_action)
  - Updated terminology in all method implementations (HQ → Coordinator, mission → project)
- ✅ Converting team_mode.py (formerly field_mode.py):
  - Updated module docstring and imports
  - Updated class name (FieldConversationHandler → TeamConversationHandler)
  - Renamed and updated all methods:
    - create_field_request → create_information_request
    - update_mission_status → update_project_dashboard
    - mark_criterion_completed (updated to use project terminology)
    - report_mission_completed → report_project_completed 
    - get_kb_section (updated to use project terminology)
    - get_mission_briefing_info → get_project_brief_info
    - get_mission_info → get_project_info
    - log_action (updated to use log_project_action)
  - Updated all references to use new terminology (field → team, mission → project)
- ✅ Converting project_storage.py (formerly mission_storage.py):
  - Updated module docstring and imports
  - Updated all enums and class names:
    - MissionRole → ProjectRole (HQ → COORDINATOR, FIELD → TEAM)
    - HQConversationMessage → CoordinatorConversationMessage
    - HQConversationStorage → CoordinatorConversationStorage
    - MissionStorageManager → ProjectStorageManager
    - MissionStorage → ProjectStorage
    - MissionNotifier → ProjectNotifier
    - ConversationMissionManager → ConversationProjectManager
  - Updated all class members and constants:
    - MISSIONS_ROOT → PROJECTS_ROOT
    - All entity constant names (MISSION_BRIEFING → PROJECT_BRIEF, etc.)
    - All file/path references (mission_briefing → project_brief, etc.)
    - Updated directory structure references (hq → coordinator, field → team)
  - Renamed all methods to use project terminology:
    - read_mission_briefing → read_project_brief 
    - write_mission_briefing → write_project_brief
    - read_mission_log → read_project_log
    - write_mission_log → write_project_log
    - read_mission_status → read_project_dashboard
    - write_mission_status → write_project_dashboard
    - read_mission_kb → read_project_kb
    - write_mission_kb → write_project_kb
    - read_hq_conversation → read_coordinator_conversation
    - append_hq_message → append_coordinator_message
    - refresh_all_mission_uis → refresh_all_project_uis
    - log_mission_event → log_project_event
    - notify_mission_update → notify_project_update
    - associate_conversation_with_mission → associate_conversation_with_project
    - get_associated_mission_id → get_associated_project_id
    - set_conversation_mission → set_conversation_project
    - get_conversation_mission → get_conversation_project
- ✅ Converting project_tools.py (formerly mission_tools.py):
  - Updated module docstring and imports to reference new modules
  - Renamed the main class from MissionTools to ProjectTools
  - Updated all methods to use project terminology:
    - get_project_info (formerly get_mission_info)
    - create_project_brief (formerly create_mission_briefing)
    - add_project_goal (formerly add_mission_goal)
    - add_kb_section (updated references inside)
    - resolve_information_request (formerly resolve_field_request)
    - create_information_request (formerly create_field_request)
    - update_project_dashboard (formerly update_mission_status)
    - mark_criterion_completed (updated to use project terminology)
    - mark_project_ready_for_working (formerly mark_mission_ready_for_field)
    - report_project_completion (formerly report_mission_completion)
    - view_coordinator_conversation (formerly view_hq_conversation)
    - delete_information_request (formerly delete_field_request)
    - detect_information_request_needs (formerly detect_field_request_needs)
    - suggest_next_action (updated to use project references throughout)
  - Updated all method implementations to use project terminology:
    - Updated all role references (field → team, hq → coordinator)
    - Updated all parameter, variable names to use project terminology
    - Updated all path references (/missions/ → /projects/)
    - Updated all documentation strings to use project terminology
    - Updated the LLM-based detection system prompt
- ✅ Converting state_inspector.py:
  - Updated module docstring and imports
  - Updated class name from MissionInspectorStateProvider to ProjectInspectorStateProvider
  - Updated metadata handling for project roles
  - Updated the setup instructions to reference coordinator and team
  - Updated formatter methods:
    - _format_hq_markdown → _format_coordinator_markdown
    - _format_field_markdown → _format_team_markdown
  - Updated all references to use project terminology:
    - mission → project
    - mission_id → project_id
    - briefing → brief
    - status → dashboard
    - field_requests → information_requests
    - view_hq_conversation → view_coordinator_conversation
    - All role references (field → team, hq → coordinator)

## Conversion Steps

### 1. Update Python File Names ✓
```bash
# Rename primary module files
git mv assistant/mission.py assistant/project.py
git mv assistant/mission_common.py assistant/project_common.py
git mv assistant/mission_data.py assistant/project_data.py
git mv assistant/mission_manager.py assistant/project_manager.py
git mv assistant/mission_storage.py assistant/project_storage.py
git mv assistant/mission_tools.py assistant/project_tools.py
git mv assistant/hq_mode.py assistant/coordinator_mode.py
git mv assistant/field_mode.py assistant/team_mode.py
```

### 2. Update all internal imports to work with new file names ✓
Files that need updates:
- chat.py
- command_processor.py
- project_common.py (formerly mission_common.py)
- coordinator_mode.py (formerly hq_mode.py)
- project.py (formerly mission.py)
- project_manager.py (formerly mission_manager.py)
- project_tools.py (formerly mission_tools.py)
- state_inspector.py
- team_mode.py (formerly field_mode.py)

### 3. Global Search and Replace ✓
Execute in order of most specific to most general:

1. **Function and Class Names: (chat.py updated ✓)**
   - `MissionManager` → `ProjectManager`
   - `MissionData` → `ProjectData`
   - `MissionTools` → `ProjectTools`
   - `MissionStorage` → `ProjectStorage`
   - `MissionBriefing` → `ProjectBrief`
   - `FieldRequest` → `InformationRequest`
   - `MissionKB` → `ProjectKB`
   - `MissionStatus` → `ProjectDashboard`
   - `MissionLog` → `ProjectLog`
   - `HQConversation` → `CoordinatorConversation`

2. **Variable and Parameter Names: (chat.py updated ✓)**
   - `mission_id` → `project_id`
   - `mission_briefing` → `project_brief`
   - `mission_kb` → `project_kb`
   - `mission_status` → `project_dashboard`
   - `field_request` → `information_request`
   - `mission_log` → `project_log`
   - `hq_conversation` → `coordinator_conversation`

3. **Import Statements: (chat.py updated ✓)**
   - `from .mission` → `from .project`
   - `from .mission_common` → `from .project_common`
   - `from .mission_data` → `from .project_data`
   - `from .mission_manager` → `from .project_manager`
   - `from .mission_storage` → `from .project_storage`
   - `from .mission_tools` → `from .project_tools`
   - `from .hq_mode` → `from .coordinator_mode`
   - `from .field_mode` → `from .team_mode`

4. **Enum and Constant Values: (chat.py updated ✓)**
   - `planning` → `planning` (no change)
   - `ready_for_field` → `ready_for_working`
   - `in_progress` → `in_progress` (no change)
   - `completed` → `completed` (no change)
   - `aborted` → `aborted` (no change)

5. **Phrases in Comments and Strings: (chat.py updated ✓)**
   - `Mission` → `Project`
   - `HQ` → `Coordinator`
   - `Field` → `Team`
   - `mission` → `project`
   - `hq` → `coordinator`
   - `field` → `team`

### 4. Update Test Files ✅
- ✅ Renamed and updated test_mission_tools.py to test_project_tools.py
  - Updated all class names, method names, and assertions
  - Fixed all imports to use project_tools instead of mission_tools
- ✅ Renamed and updated test_mission_storage.py to test_project_storage.py
  - Updated all class imports (ProjectStorage, ProjectStorageManager)
  - Updated test data creation methods 
  - Updated assertions to validate project-related data
- ✅ Renamed and updated test_field_mode.py to test_team_mode.py
  - Updated all mock classes with new terminology (ProjectRole, ProjectBrief, etc)
  - Renamed the MockFieldConversationHandler to MockTeamConversationHandler
  - Updated all method names (create_field_request → create_information_request)
  - Updated the test class name and all test methods

Still need to update:
- ✅ test_artifact_messaging.py - Completed with all terminology changes
- ✅ test_setup_mode.py - Completed with all terminology changes
- ❓ test_invitation_system.py - Started updating but needs more work to fix tests
- test_artifact_loading.py

### 5. Update Documentation
- ✅ DESIGN.md - Completed with all terminology changes
- ✅ DEV_GUIDE.md - Completed with all terminology changes
- ✅ README.md - Completed with all terminology changes
- Any inline documentation or comments

### 6. Verify Code Integrity
```bash
# Run linting and type checks
make lint # ✅ All checks passed!

# Type checks
make type-check # ✅ Successfully passes for updated test files (test_artifact_messaging.py)
                # ❓ Still has errors in test_invitation_system.py that need fixing

# Run tests to ensure functionality is preserved
make test # ✅ test_artifact_messaging.py passes all tests
         # ❓ test_invitation_system.py needs more work
         # ❌ test_artifact_loading.py still needs updating
```

Currently, we've successfully converted all the core code files and some of the test files with the mission->project terminology. The linting checks pass, and type checks pass for the updated test files but still fail for test_invitation_system.py. We need to finish updating the remaining test files to achieve full compatibility.

### 7. Update References in Other Projects
Identify and update any external projects that reference this library.