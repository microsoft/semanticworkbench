# Plan of Action: Implement Automatic Role Detection with Team Workspaces

## Overview

This Plan of Action details the necessary changes to eliminate the need for explicit `/start` and `/join` commands by implementing automatic role detection and dedicated team workspaces. Rather than requiring users to run specific commands to set up their roles, the system will automatically:

1. Designate any new conversation as a Coordinator by default
2. Create a separate shareable team workspace for project collaboration
3. Generate shareable team invitation links for accessing the workspace
4. Automatically set up shared conversations as Team members
5. Handle all project associations and file synchronization without manual commands

This approach creates a more intuitive user experience and aligns with standard sharing patterns used throughout the Semantic Workbench.

## Revised Architecture

In this approach, the original user conversation is the "coordinator conversation" where the project owner works directly with the assistant. We'll create a separate "shareable team conversation" that serves as a clean workspace for team members:

1. **Original Conversation = Coordinator**: The user's original conversation is their primary workspace and serves as the coordinator hub
2. **New Conversation = Team Workspace**: We create a separate shareable conversation with proper setup for team members

The workflow will be:
1. User starts a conversation with the assistant (this becomes the coordinator conversation)
2. Assistant creates a new "shareable team conversation" via the API
3. Assistant sets up this team conversation with the proper project data and setup
4. Assistant creates a share link for the team conversation
5. Assistant provides the share link to the user in the coordinator conversation
6. The coordinator shares this link with team members who need to collaborate
7. When team members open the link, they join a clean workspace configured for the project

This approach gives the coordinator their own private space to manage the project while giving team members a clean, focused environment for collaboration.

## Implementation Steps

### 1. Update Configuration Welcome Message

**File:** `/data/repos/semanticworkbench/assistants/project-assistant/assistant/configs/default.py`

Update the welcome message in the AssistantConfigModel to remove references to `/start` and `/join` commands:

```python
welcome_message: Annotated[
    str,
    Field(
        title="Initial Setup Welcome Message",
        description="The message displayed when the assistant first starts, before any role is assigned. This explains the setup process.",
    ),
    UISchema(widget="textarea"),
] = """# Welcome to the Project Assistant

This assistant helps coordinate project activities between Coordinators and Team members.

This conversation is for project coordinators. Share the generated invitation link with team members to collaborate on your project.

Type `/help` for more information on available commands."""
```

### 2. Enhance Project Manager with Team Conversation Functions

**File:** `/data/repos/semanticworkbench/assistants/project-assistant/assistant/project_manager.py`

Add new methods to the `ProjectManager` class to support creating and sharing a team conversation:

```python
@staticmethod
async def create_team_conversation(
    context: ConversationContext,
    project_id: str,
    project_name: str = "Project"
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Creates a shareable team conversation for the project and returns a share link.
    
    This method:
    1. Creates a new conversation via the Workbench API with the current user as owner
    2. Sets up the conversation with project metadata
    3. Creates a share link for the conversation
    
    Args:
        context: Current conversation context (coordinator conversation)
        project_id: ID of the project
        project_name: Name of the project for the conversation title
        
    Returns:
        Tuple of (success, conversation_id, share_url)
    """
    try:
        from semantic_workbench_api_model import workbench_model
        
        # Get the current user ID for ownership
        current_user_id, _ = await get_current_user(context)
        if not current_user_id:
            logger.error("Cannot create team conversation: no user found in conversation")
            return False, None, None
        
        # Create a new conversation via the API
        new_conversation = workbench_model.NewConversation(
            title=f"{project_name} - Team Workspace",
            metadata={
                "project_id": project_id,
                "is_team_workspace": True,
                "created_by": str(context.id)
            }
        )
        
        # Access the conversation client
        conversations_client = context._workbench_client.for_conversations()
        
        # Create the new conversation with the current user as owner
        conversation = await conversations_client.create_conversation_with_owner(
            new_conversation=new_conversation,
            owner_id=current_user_id
        )
        
        if not conversation or not conversation.id:
            logger.error("Failed to create team conversation")
            return False, None, None
            
        # Create a share for this new conversation
        share_success, share_url = await ProjectManager.create_share_for_conversation(
            context=context,
            conversation_id=str(conversation.id),
            project_id=project_id,
            project_name=project_name,
            owner_id=current_user_id
        )
        
        if not share_success or not share_url:
            logger.error("Failed to create share for team conversation")
            return True, str(conversation.id), None
            
        return True, str(conversation.id), share_url
            
    except Exception as e:
        logger.exception(f"Error creating team conversation: {e}")
        return False, None, None
        
@staticmethod
async def create_share_for_conversation(
    context: ConversationContext,
    conversation_id: str,
    project_id: str,
    project_name: str = "Project",
    owner_id: str = None
) -> Tuple[bool, Optional[str]]:
    """
    Creates a shareable link for the specified conversation.
    
    Args:
        context: Current conversation context
        conversation_id: ID of the conversation to share
        project_id: ID of the project
        project_name: Name of the project
        owner_id: Optional owner ID for the share (defaults to the current user)
        
    Returns:
        Tuple of (success, share_url)
    """
    try:
        from semantic_workbench_api_model import workbench_model
        
        # Get the owner ID if not provided
        if not owner_id:
            owner_id, _ = await get_current_user(context)
            if not owner_id:
                logger.error("Cannot create share: no user found in conversation")
                return False, None
        
        # Create the conversation share model
        new_share = workbench_model.NewConversationShare(
            conversation_id=uuid.UUID(conversation_id),
            label=f"Join Project: {project_name}",
            conversation_permission=workbench_model.ConversationPermission.read_write,
            metadata={"project_id": project_id}
        )
        
        # Access the conversation client
        conversations_client = context._workbench_client.for_conversations()
        
        # Create the share with the specified owner
        share = await conversations_client.create_conversation_share_with_owner(
            new_conversation_share=new_share,
            owner_id=owner_id
        )
        
        if not share or not share.conversation_share_id:
            logger.error("Failed to create share")
            return False, None
            
        # Generate a shareable URL
        base_url = str(context._workbench_client.base_url)
        if base_url.endswith("/api"):
            base_url = base_url[:-4]
            
        share_url = f"{base_url}/s/{share.conversation_share_id}"
        
        # Store the share URL in project storage for future reference
        project_storage = ProjectStorage.get_project_storage(project_id)
        if "team_workspace" not in project_storage:
            project_storage["team_workspace"] = {}
        
        project_storage["team_workspace"] = {
            "conversation_id": conversation_id,
            "share_id": str(share.conversation_share_id),
            "share_url": share_url
        }
        
        ProjectStorage.write_project_storage(project_id, project_storage)
        
        return True, share_url
        
    except Exception as e:
        logger.exception(f"Error creating share link: {e}")
        return False, None
```

### 3. Modify Conversation Creation Handler

**File:** `/data/repos/semanticworkbench/assistants/project-assistant/assistant/chat.py`

Update the `on_conversation_created` handler to automatically initialize projects and create team workspaces:

```python
@assistant.events.conversation.on_created
async def on_conversation_created(context: ConversationContext) -> None:
    """
    Handle the event triggered when the assistant is added to a conversation.
    
    This now automatically sets up the conversation based on its origin:
    - New conversations: Coordinator mode, new project created automatically with team workspace
    - Shared/cloned conversations: Team mode if from a share, connected to the original project
    - Team workspace conversations: These are generated by the system, not directly entered by users
    """
    try:
        # Get conversation to access metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        
        # Check what type of conversation this is
        is_from_share = bool(metadata.get("imported_from_conversation_id"))
        is_team_workspace = bool(metadata.get("is_team_workspace"))
        
        # Detect whether this is a Coordinator or Team conversation
        role = await detect_assistant_role(context)
        
        # Store the role in conversation metadata
        metadata["project_role"] = role
        metadata["assistant_mode"] = role
        metadata["setup_complete"] = True
        
        # Handle based on conversation type
        if is_team_workspace:
            # This is a system-generated team workspace
            # We don't need to do anything special here as it was already set up
            # by the coordinator conversation that created it
            
            # The welcome message will be shown to team members who join through a share
            config = await assistant_config.get(context.assistant)
            welcome_message = (
                "# Team Workspace\n\n"
                "This is a dedicated team workspace for collaborating on the project.\n\n"
                "Files and information shared here will be synchronized with all team members."
            )
            
        elif is_from_share:
            # This is a team member joining through a share link
            
            # Get the project ID from metadata 
            project_id = metadata.get("project_id")
            
            if project_id:
                # Join the project automatically
                await ProjectManager.join_project(context, project_id, ProjectRole.TEAM)
                
                # Synchronize files automatically
                from .project_files import ProjectFileManager
                await ProjectFileManager.synchronize_files_to_team_conversation(
                    context=context, project_id=project_id
                )
                
                # Send welcome message for team member using config
                config = await assistant_config.get(context.assistant)
                welcome_message = config.team_config.welcome_message
            else:
                # If we can't determine the project ID, treat as a new conversation
                success, project_id = await ProjectManager.create_project(context)
                welcome_message = "# New Project Created\n\nI've automatically set up this conversation as a Project Coordinator."
        else:
            # This is a new Coordinator conversation
            
            # Create a new project automatically
            success, project_id = await ProjectManager.create_project(context)
            
            if success:
                # Get the project name (from brief if it exists)
                brief = ProjectStorage.read_project_brief(project_id)
                project_name = brief.project_name if brief else "Project"
                
                # Create a team workspace and share link
                success, team_conversation_id, share_url = await ProjectManager.create_team_conversation(
                    context=context,
                    project_id=project_id,
                    project_name=project_name
                )
                
                if success and share_url:
                    # Store the team workspace info in conversation metadata
                    metadata["team_workspace_id"] = team_conversation_id
                    metadata["team_share_url"] = share_url
                    
                    # Send welcome message with the share link included
                    config = await assistant_config.get(context.assistant)
                    
                    # Use the coordinator welcome message from config and append share link info
                    welcome_message = config.coordinator_config.welcome_message + (
                        "\n\n## Team Invitation Link\n\n"
                        f"Share this link with team members to invite them to your project:\n\n"
                        f"`{share_url}`\n\n"
                        "When team members open this link, they'll join a dedicated workspace "
                        "with access to all project files and information."
                    )
                else:
                    # Fallback welcome message if team workspace creation fails
                    config = await assistant_config.get(context.assistant)
                    welcome_message = config.coordinator_config.welcome_message
            else:
                # Fallback if project creation fails
                config = await assistant_config.get(context.assistant)
                welcome_message = config.welcome_message

        # Update conversation metadata
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="project_role", event="updated", state=None)
        )
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="assistant_mode", event="updated", state=None)
        )
        await context.send_conversation_state_event(
            AssistantStateEvent(state_id="setup_complete", event="updated", state=None)
        )

        # Send the welcome message
        await context.send_messages(
            NewConversationMessage(
                content=welcome_message,
                message_type=MessageType.chat,
                metadata={"generated_content": False},
            )
        )

        # Update UI inspector
        await ProjectStorage.refresh_current_ui(context)

    except Exception as e:
        logger.exception(f"Error in conversation created handler: {e}")

        # Fallback to welcome message on error
        config = await assistant_config.get(context.assistant)
        
        # Use the initial welcome message without any project-specific information
        await context.send_messages(
            NewConversationMessage(
                content=config.welcome_message,
                message_type=MessageType.chat,
                metadata={"generated_content": False},
            )
        )
```

### 4. Update Role Detection Logic

**File:** `/data/repos/semanticworkbench/assistants/project-assistant/assistant/chat.py`
**Method:** `detect_assistant_role()`

Modify this method to include team workspace detection:

```python
async def detect_assistant_role(context: ConversationContext) -> str:
    """
    Detects whether this conversation is in Coordinator Mode or Team Mode.

    New logic:
    - Original conversations (not created from shares) are Coordinators
    - Conversations created from shares are Team members
    - Team workspace conversations are treated as a special type of team conversation
    - Existing role detection serves as fallback

    Returns:
        "coordinator" if in Coordinator Mode, "team" if in Team Mode
    """
    try:
        # First check if there's already a role set in project storage
        role = await ConversationProjectManager.get_conversation_role(context)
        if role:
            return role.value

        # Get conversation to check its metadata
        conversation = await context.get_conversation()
        metadata = conversation.metadata or {}
        
        # Check if this is a team workspace created for a project
        if metadata.get("is_team_workspace"):
            logger.info(f"Detected team role from team workspace marker")
            return "team"
            
        # Check if this conversation was created from a share/duplicate
        if metadata.get("imported_from_conversation_id"):
            # Conversations created from shares are always Team members
            logger.info(f"Detected team role from share origin")
            return "team"

        # Get project ID
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            # No project association yet, default to Coordinator
            return "coordinator"

        # Check if this conversation created a project brief
        briefing = ProjectStorage.read_project_brief(project_id)

        # If the briefing was created by this conversation, we're in Coordinator Mode
        if briefing and briefing.conversation_id == str(context.id):
            return "coordinator"

        # Otherwise, if we have a project association but didn't create the briefing,
        # we're likely in Team Mode
        return "team"

    except Exception as e:
        logger.exception(f"Error detecting assistant role: {e}")
        # Default to Coordinator Mode if detection fails
        return "coordinator"
```

### 5. Update State Inspector to Display Share URL

**File:** `/data/repos/semanticworkbench/assistants/project-assistant/assistant/state_inspector.py`

Modify the state inspector to display the team workspace share URL in the coordinator view:

```python
# Inside the get_inspector_content method
if role == ProjectRole.COORDINATOR:
    # Get conversation metadata
    conversation = await context.get_conversation()
    metadata = conversation.metadata or {}

    # Add team workspace share URL if available
    share_url = metadata.get("team_share_url")
    if share_url:
        content += f"\n\n### Team Invitation Link\n\nShare this link with team members:\n\n`{share_url}`"
    else:
        # In case the automatic share creation failed, check project storage
        project_id = await ProjectManager.get_project_id(context)
        if project_id:
            project_storage = ProjectStorage.get_project_storage(project_id)
            if "team_workspace" in project_storage and "share_url" in project_storage["team_workspace"]:
                share_url = project_storage["team_workspace"]["share_url"]
                content += f"\n\n### Team Invitation Link\n\nShare this link with team members:\n\n`{share_url}`"
```

### 6. Remove Unnecessary Commands

**File:** `/data/repos/semanticworkbench/assistants/project-assistant/assistant/command_processor.py`

1. Remove the `/start` and `/join` commands from the `COMMANDS` dictionary:

```python
# Remove these entries from the COMMANDS dictionary
# "start": CommandHandler(start_project, "Create a new project as Coordinator", "start"),
# "join": CommandHandler(join_project, "Join an existing project as a Team member", "join <project_id>"),
```

2. Update the help command to provide appropriate guidance for each role:

```python
# For coordinator help
help_text += (
    "As a Coordinator, you are responsible for defining the project and responding to team member requests. "
    "Share the team invitation link displayed in the project status with team members to invite them."
)

# For team member help
help_text += (
    "As a Team member, you can access project information, request information, and report progress on project goals. "
    "Use `/project-info` to see the current project status and `/request-info` to ask for information from the Coordinator."
)
```

3. Delete or comment out the `start_project` and `join_project` functions since they will no longer be used.

## Testing Plan

1. Test new conversation creation:
   - Verify automatic project creation works correctly
   - Verify team workspace creation occurs automatically
   - Verify share link generation works automatically
   - Verify share URL is displayed in the UI inspector

2. Test team workspace functionality:
   - Verify the team workspace is configured correctly with project metadata
   - Verify the team workspace is properly shared with correct permissions
   - Verify the coordinator can access the team workspace if needed

3. Test team conversation creation via share link:
   - Verify redeeming the share creates a properly configured conversation
   - Verify project association is handled correctly on redemption
   - Verify files are synchronized automatically

4. Test full workflow:
   - Create a coordinator conversation and check for automatic team workspace creation and share link
   - Use the share link to create multiple team conversations
   - Verify files sync correctly in all directions
   - Verify all team conversations show the expected project information

## Benefits

1. **Zero-setup experience**: Users never need to run setup commands
2. **Always ready**: Share links are ready immediately without explicit commands
3. **Reduced user friction**: Team members join with just a click, never needing to copy/paste project IDs
4. **Consistent with platform**: Uses standard Workbench sharing mechanisms that users are familiar with
5. **Separation of responsibilities**: Coordinator has their own private workspace while team members get a clean, dedicated collaboration space
6. **Improved organization**: Project files and collaboration happen in a dedicated workspace, keeping the coordinator's conversation free of clutter