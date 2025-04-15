"""
Project management logic for working with project data.

This module provides the core business logic for working with project data
without relying on the artifact abstraction.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from .logging import logger
from .project_data import (
    InformationRequest,
    LogEntry,
    LogEntryType,
    ProjectBrief,
    ProjectGoal,
    ProjectInfo,
    ProjectLog,
    ProjectState,
    ProjectWhiteboard,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from .project_storage import (
    ConversationProjectManager,
    ProjectNotifier,
    ProjectRole,
    ProjectStorage,
    ProjectStorageManager,
)
from .utils import get_current_user, require_current_user


class ProjectManager:
    """
    Manages the creation, modification, and lifecycle of projects.

    The ProjectManager provides a centralized set of operations for working with project data.
    It handles all the core business logic for interacting with projects, ensuring that
    operations are performed consistently and following the proper rules and constraints.

    This class implements the primary interface for both Coordinators and team members to interact
    with project entities like briefs, information requests, and knowledge bases. It abstracts
    away the storage details and provides a clean API for project operations.

    All methods are implemented as static methods to facilitate easy calling from
    different parts of the codebase without requiring instance creation.
    """

    @staticmethod
    async def create_team_conversation(
        context: ConversationContext, project_id: str, project_name: str = "Project"
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Creates a new shareable team conversation template.

        This creates a new conversation owned by the same user as the current conversation,
        intended to be used as a shareable team conversation template. This is NOT a
        conversation that anyone will directly use. Instead, it's a template that gets
        copied when team members redeem the share URL, creating their own individual
        team conversations.

        The conversation is tagged with metadata indicating its purpose and gets a
        share URL that can be used by team members to join the project.

        Args:
            context: Current conversation context
            project_id: ID of the project
            project_name: Name of the project

        Returns:
            Tuple of (success, conversation_id, share_url) where:
            - success: Boolean indicating if the creation was successful
            - conversation_id: ID of the created shareable team conversation
            - share_url: URL for joining the project and creating a team conversation
        """
        try:
            # Get the current user ID to set as owner
            user_id, _ = await get_current_user(context)
            if not user_id:
                logger.error("Cannot create team conversation: no user found")
                return False, None, None

            # Create a new conversation using the client
            from semantic_workbench_api_model.workbench_model import NewConversation

            # Create the new conversation with appropriate metadata
            new_conversation = NewConversation(
                title=f"{project_name}",
                metadata={
                    "is_team_conversation": True,
                    "project_id": project_id,
                    "setup_complete": True,
                    "project_role": "team",
                    "assistant_mode": "team",
                },
            )

            # Use the conversations client to create the conversation with owner
            client = context._conversations_client
            conversation = await client.create_conversation_with_owner(
                new_conversation=new_conversation, owner_id=user_id
            )

            if not conversation or not conversation.id:
                logger.error("Failed to create team conversation")
                return False, None, None

            logger.info(f"Created team conversation: {conversation.id}")

            # Create a share for the new conversation
            success, share_url = await ProjectManager.create_share_for_conversation(
                context=context,
                conversation_id=conversation.id,
                project_id=project_id,
                project_name=project_name,
                owner_id=user_id,
            )

            if not success or not share_url:
                logger.warning(f"Created team conversation but failed to create share: {conversation.id}")
                return True, str(conversation.id), None

            # Store team conversation info in ProjectInfo
            try:
                # Read existing project info
                project_info = ProjectStorage.read_project_info(project_id)

                if project_info:
                    # Update with team conversation data
                    project_info.team_conversation_id = str(conversation.id)
                    project_info.share_url = share_url
                    project_info.updated_at = datetime.utcnow()

                    # Save updated project info
                    ProjectStorage.write_project_info(project_id, project_info)
                    logger.info(f"Updated project info with team conversation: {conversation.id}")
                else:
                    logger.warning(f"Project info not found for project {project_id}")
            except Exception as e:
                logger.warning(f"Failed to update project info with team conversation: {e}")

            # Store the share URL in the conversation's metadata
            from semantic_workbench_api_model.workbench_model import AssistantStateEvent

            # Create a temporary context for the team conversation to update its metadata
            from .conversation_clients import ConversationClientManager

            team_context = await ConversationClientManager.create_temporary_context_for_conversation(
                source_context=context, target_conversation_id=str(conversation.id)
            )

            if team_context:
                # Update the team conversation's metadata with the share URL
                await team_context.send_conversation_state_event(
                    AssistantStateEvent(state_id="share_url", event="updated", state=None)
                )

            return True, str(conversation.id), share_url

        except Exception as e:
            logger.exception(f"Error creating team conversation: {e}")
            return False, None, None

    @staticmethod
    async def create_share_for_conversation(
        context: ConversationContext,
        conversation_id: uuid.UUID,
        project_id: str,
        project_name: str = "Project",
        owner_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Creates a share for the specified conversation.

        Args:
            context: Current conversation context
            conversation_id: ID of the conversation to share
            project_id: ID of the project
            project_name: Name of the project
            owner_id: Optional ID of the owner (defaults to current user)

        Returns:
            Tuple of (success, share_url) where:
            - success: Boolean indicating if the share creation was successful
            - share_url: URL for the conversation share
        """
        try:
            # Get the owner ID if not provided
            if not owner_id:
                owner_id, _ = await get_current_user(context)
                if not owner_id:
                    logger.error("Cannot create conversation share: no user found")
                    return False, None

            # Create the share using the client
            from semantic_workbench_api_model.workbench_model import (
                ConversationPermission,
                NewConversationShare,
            )

            new_share = NewConversationShare(
                conversation_id=conversation_id,
                label=f"{project_name}",
                conversation_permission=ConversationPermission.read,
                metadata={
                    "project_id": project_id,
                    "is_team_conversation": True,
                    "showDuplicateAction": True,
                    "show_duplicate_action": True,
                },
            )

            # Use the conversations client to create the share with owner
            client = context._conversations_client
            share = await client.create_conversation_share_with_owner(
                new_conversation_share=new_share, owner_id=owner_id
            )

            if not share:
                logger.error(f"Failed to create share for conversation: {conversation_id}")
                return False, None

            # Return the share URL
            url = f"/conversation-share/{share.id}/redeem"
            logger.info(f"Created share for conversation {conversation_id}: {url}")
            return True, url

        except Exception as e:
            logger.exception(f"Error creating conversation share: {e}")
            return False, None

    @staticmethod
    async def create_project(context: ConversationContext) -> Tuple[bool, str]:
        """
        Creates a new project and associates the current conversation with it.

        This is the initial step in project creation. It:
        1. Generates a unique project ID
        2. Associates the current conversation with that project
        3. Sets the current conversation as Coordinator for the project
        4. Creates empty project data structures (brief, whiteboard, etc.)
        5. Logs the project creation event

        After creating a project, the Coordinator should proceed to create a project brief
        with specific goals and success criteria.

        Args:
            context: Current conversation context containing user/assistant information

        Returns:
            Tuple of (success, project_id) where:
            - success: Boolean indicating if the creation was successful
            - project_id: If successful, the UUID of the newly created project
        """
        try:
            # Generate a unique project ID
            project_id = str(uuid.uuid4())
            logger.info(f"Starting project creation with new ID: {project_id}")

            # Create the project directory structure first
            project_dir = ProjectStorageManager.get_project_dir(project_id)
            logger.info(f"Created project directory: {project_dir}")

            # Create and save the initial project info
            from .project_data import ProjectInfo

            project_info = ProjectInfo(
                project_id=project_id, project_name="New Project", coordinator_conversation_id=str(context.id)
            )

            # Save the project info
            ProjectStorage.write_project_info(project_id, project_info)
            logger.info(f"Created and saved project info: {project_info}")

            # Associate the conversation with the project
            logger.info(f"Associating conversation {context.id} with project {project_id}")
            await ConversationProjectManager.associate_conversation_with_project(context, project_id)

            # Set this conversation as the Coordinator
            logger.info(f"Setting conversation {context.id} as Coordinator for project {project_id}")
            await ConversationProjectManager.set_conversation_role(context, project_id, ProjectRole.COORDINATOR)

            # Ensure linked_conversations directory exists
            linked_dir = ProjectStorageManager.get_linked_conversations_dir(project_id)
            logger.info(f"Ensured linked_conversations directory exists: {linked_dir}")

            logger.info(f"Successfully created new project {project_id} for conversation {context.id}")
            return True, project_id

        except Exception as e:
            logger.exception(f"Error creating project: {e}")
            return False, ""

    @staticmethod
    async def join_project(
        context: ConversationContext,
        project_id: str,
        role: ProjectRole = ProjectRole.TEAM,
    ) -> bool:
        """
        Joins an existing project.

        Args:
            context: Current conversation context
            project_id: ID of the project to join
            role: Role for this conversation (COORDINATOR or TEAM)

        Returns:
            True if joined successfully, False otherwise
        """
        try:
            # Check if project exists
            if not ProjectStorageManager.project_exists(project_id):
                logger.error(f"Cannot join project: project {project_id} does not exist")
                return False

            # Associate the conversation with the project
            await ConversationProjectManager.associate_conversation_with_project(context, project_id)

            # Set the conversation role
            await ConversationProjectManager.set_conversation_role(context, project_id, role)

            logger.info(f"Joined project {project_id} as {role.value}")
            return True

        except Exception as e:
            logger.exception(f"Error joining project: {e}")
            return False

    @staticmethod
    async def get_project_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the project ID associated with the current conversation.

        Every conversation that's part of a project has an associated project ID.
        This method retrieves that ID, which is used for accessing project-related
        data structures.

        Args:
            context: Current conversation context

        Returns:
            The project ID string if the conversation is part of a project, None otherwise
        """
        return await ConversationProjectManager.get_associated_project_id(context)

    @staticmethod
    async def get_project_role(context: ConversationContext) -> Optional[ProjectRole]:
        """
        Gets the role of the current conversation in its project.

        Each conversation participating in a project has a specific role:
        - COORDINATOR: The primary conversation that created and manages the project
        - TEAM: Conversations where team members are carrying out the project tasks

        Args:
            context: Current conversation context

        Returns:
            The role (ProjectRole.COORDINATOR or ProjectRole.TEAM) if the conversation
            is part of a project, None otherwise
        """
        return await ConversationProjectManager.get_conversation_role(context)

    @staticmethod
    async def get_project_brief(context: ConversationContext) -> Optional[ProjectBrief]:
        """
        Gets the project brief for the current conversation's project.

        The project brief contains the core information about the project:
        name, description, goals, and success criteria. This is the central
        document that defines what the project is trying to accomplish.

        Args:
            context: Current conversation context

        Returns:
            The ProjectBrief object if found, None if the conversation is not
            part of a project or if no brief has been created yet
        """
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            return None

        return ProjectStorage.read_project_brief(project_id)

    @staticmethod
    async def create_project_brief(
        context: ConversationContext,
        project_name: str,
        project_description: str,
        goals: Optional[List[Dict]] = None,
        timeline: Optional[str] = None,
        additional_context: Optional[str] = None,
        send_notification: bool = True,
    ) -> Tuple[bool, Optional[ProjectBrief]]:
        """
        Creates a new project brief for the current project.

        The project brief is the primary document that defines the project's
        purpose, goals, and success criteria. Creating a brief is typically
        done by the Coordinator during the planning phase, and it should be completed before
        team members are invited to join the project.

        If goals are provided, they should be a list of dictionaries with the format:
        [
            {
                "name": "Goal name",
                "description": "Detailed description of the goal",
                "success_criteria": [
                    "First criterion to meet for this goal",
                    "Second criterion to meet for this goal"
                ]
            },
            ...
        ]

        Args:
            context: Current conversation context
            project_name: Short, descriptive name for the project
            project_description: Comprehensive description of the project's purpose
            goals: Optional list of goals with success criteria (see format above)
            timeline: Optional information about project timeline/deadlines
            additional_context: Optional additional information relevant to the project
            send_notification: Whether to send a notification about the brief creation (default: True)

        Returns:
            Tuple of (success, project_brief) where:
            - success: Boolean indicating if brief creation was successful
            - project_brief: The created ProjectBrief object if successful, None otherwise
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot create brief: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "create brief")
            if not current_user_id:
                return False, None

            # Create project goals
            project_goals = []
            if goals:
                for i, goal_data in enumerate(goals):
                    goal = ProjectGoal(
                        name=goal_data.get("name", f"Goal {i + 1}"),
                        description=goal_data.get("description", ""),
                        priority=goal_data.get("priority", i + 1),
                        success_criteria=[],
                    )

                    # Add success criteria
                    criteria = goal_data.get("success_criteria", [])
                    for criterion in criteria:
                        goal.success_criteria.append(SuccessCriterion(description=criterion))

                    project_goals.append(goal)

            # Create the project brief
            brief = ProjectBrief(
                project_name=project_name,
                project_description=project_description,
                goals=project_goals,
                timeline=timeline,
                additional_context=additional_context,
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            # Save the brief
            ProjectStorage.write_project_brief(project_id, brief)

            # Log the creation
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.BRIEFING_CREATED.value,
                message=f"Created project brief: {project_name}",
            )

            # Only notify if send_notification is True
            if send_notification:
                # Notify linked conversations
                await ProjectNotifier.notify_project_update(
                    context=context,
                    project_id=project_id,
                    update_type="brief",
                    message=f"Project brief created: {project_name}",
                )

            return True, brief

        except Exception as e:
            logger.exception(f"Error creating project brief: {e}")
            return False, None

    @staticmethod
    async def update_project_brief(
        context: ConversationContext,
        updates: Dict[str, Any],
        send_notification: bool = True,
    ) -> bool:
        """
        Updates an existing project brief.

        Args:
            context: Current conversation context
            updates: Dictionary of fields to update
            send_notification: Whether to send a notification about the brief update (default: True)

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot update brief: no project associated with this conversation")
                return False

            # Get user information
            current_user_id = await require_current_user(context, "update brief")
            if not current_user_id:
                return False

            # Load existing brief
            brief = ProjectStorage.read_project_brief(project_id)
            if not brief:
                logger.error(f"Cannot update brief: no brief found for project {project_id}")
                return False

            # Apply updates, skipping immutable fields
            any_fields_updated = False
            immutable_fields = [
                "created_by",
                "conversation_id",
                "created_at",
                "version",
            ]

            for field, value in updates.items():
                if hasattr(brief, field) and field not in immutable_fields:
                    setattr(brief, field, value)
                    any_fields_updated = True

            if not any_fields_updated:
                logger.info("No updates applied to brief")
                return True

            # Update metadata
            brief.updated_at = datetime.utcnow()
            brief.updated_by = current_user_id
            brief.version += 1

            # Save the updated brief
            ProjectStorage.write_project_brief(project_id, brief)

            # Log the update
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Updated project brief: {brief.project_name}",
            )

            # Only notify if send_notification is True
            if send_notification:
                # Notify linked conversations
                await ProjectNotifier.notify_project_update(
                    context=context,
                    project_id=project_id,
                    update_type="brief",
                    message=f"Project brief updated: {brief.project_name}",
                )

            return True

        except Exception as e:
            logger.exception(f"Error updating project brief: {e}")
            return False

    @staticmethod
    async def get_project_state(
        context: ConversationContext,
    ) -> Optional[ProjectState]:
        """Gets the project state for the current conversation's project."""
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            return None

        # Get the project info which contains state information
        project_info = ProjectStorage.read_project_info(project_id)
        if not project_info:
            return None

        return project_info.state

    @staticmethod
    async def update_project_state(
        context: ConversationContext,
        state: Optional[str] = None,
        status_message: Optional[str] = None,
    ) -> Tuple[bool, Optional[ProjectInfo]]:
        """
        Updates the project state and status message.

        Args:
            context: Current conversation context
            state: Optional project state
            status_message: Optional status message

        Returns:
            Tuple of (success, project_info)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot update project state: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update project state")
            if not current_user_id:
                return False, None

            # Get existing project info
            project_info = ProjectStorage.read_project_info(project_id)
            if not project_info:
                logger.error(f"Cannot update project state: no project info found for {project_id}")
                return False, None

            # Apply updates
            if state:
                project_info.state = ProjectState(state)

            if status_message:
                project_info.status_message = status_message

            # Update metadata
            project_info.updated_at = datetime.utcnow()

            # Save the project info
            ProjectStorage.write_project_info(project_id, project_info)

            # Log the update
            event_type = LogEntryType.STATUS_CHANGED
            message = f"Updated project state to {project_info.state.value}"

            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=event_type.value,
                message=message,
                metadata={
                    "state": project_info.state.value,
                    "status_message": status_message,
                },
            )

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="project_state",
                message=f"Project state updated: {project_info.state.value}",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error updating project state: {e}")
            return False, None

    @staticmethod
    async def get_information_requests(
        context: ConversationContext,
    ) -> List[InformationRequest]:
        """Gets all information requests for the current conversation's project."""
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            return []

        return ProjectStorage.get_all_information_requests(project_id)

    @staticmethod
    async def create_information_request(
        context: ConversationContext,
        title: str,
        description: str,
        priority: RequestPriority = RequestPriority.MEDIUM,
        related_goal_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[InformationRequest]]:
        """
        Creates a new information request.

        Args:
            context: Current conversation context
            title: Title of the request
            description: Description of the request
            priority: Priority level
            related_goal_ids: Optional list of related goal IDs

        Returns:
            Tuple of (success, information_request)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot create information request: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "create information request")
            if not current_user_id:
                return False, None

            # Create the information request
            information_request = InformationRequest(
                title=title,
                description=description,
                priority=priority,
                related_goal_ids=related_goal_ids or [],
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            # Save the request
            ProjectStorage.write_information_request(project_id, information_request)

            # Log the creation
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.REQUEST_CREATED.value,
                message=f"Created information request: {title}",
                related_entity_id=information_request.request_id,
                metadata={
                    "priority": priority.value,
                    "request_id": information_request.request_id,
                },
            )

            # For high priority requests, we could update project info or add an indicator
            # in the future if needed

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="information_request",
                message=f"New information request: {title} (Priority: {priority.value})",
            )

            # Update all project UI inspectors
            await ProjectStorage.refresh_all_project_uis(context, project_id)

            return True, information_request

        except Exception as e:
            logger.exception(f"Error creating information request: {e}")
            return False, None

    @staticmethod
    async def update_information_request(
        context: ConversationContext,
        request_id: str,
        updates: Dict[str, Any],
    ) -> Tuple[bool, Optional[InformationRequest]]:
        """
        Updates an existing information request.

        Args:
            context: Current conversation context
            request_id: ID of the request to update
            updates: Dictionary of fields to update

        Returns:
            Tuple of (success, information_request)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot update information request: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update information request")
            if not current_user_id:
                return False, None

            # Get the information request
            information_request = ProjectStorage.read_information_request(project_id, request_id)
            if not information_request:
                logger.error(f"Information request {request_id} not found")
                return False, None

            # Apply updates, skipping protected fields
            updated = False
            protected_fields = [
                "request_id",
                "created_by",
                "created_at",
                "conversation_id",
                "version",
            ]

            for field, value in updates.items():
                if hasattr(information_request, field) and field not in protected_fields:
                    # Special handling for status changes
                    if field == "status" and information_request.status != value:
                        # Add an update to the history
                        information_request.updates.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "user_id": current_user_id,
                            "message": f"Status changed from {information_request.status.value} to {value.value}",
                            "status": value.value,
                        })

                    setattr(information_request, field, value)
                    updated = True

            if not updated:
                logger.info(f"No updates applied to information request {request_id}")
                return True, information_request

            # Update metadata
            information_request.updated_at = datetime.utcnow()
            information_request.updated_by = current_user_id
            information_request.version += 1

            # Save the updated request
            ProjectStorage.write_information_request(project_id, information_request)

            # Log the update
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.REQUEST_UPDATED.value,
                message=f"Updated information request: {information_request.title}",
                related_entity_id=information_request.request_id,
            )

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="information_request_updated",
                message=f"Information request updated: {information_request.title}",
            )

            return True, information_request

        except Exception as e:
            logger.exception(f"Error updating information request: {e}")
            return False, None

    @staticmethod
    async def resolve_information_request(
        context: ConversationContext,
        request_id: str,
        resolution: str,
    ) -> Tuple[bool, Optional[InformationRequest]]:
        """
        Resolves an information request.

        Args:
            context: Current conversation context
            request_id: ID of the request to resolve
            resolution: Resolution information

        Returns:
            Tuple of (success, information_request)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot resolve information request: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "resolve information request")
            if not current_user_id:
                return False, None

            # Get the information request
            information_request = ProjectStorage.read_information_request(project_id, request_id)
            if not information_request:
                # Try to find it in all requests
                all_requests = ProjectStorage.get_all_information_requests(project_id)
                for request in all_requests:
                    if request.request_id == request_id:
                        information_request = request
                        break

                if not information_request:
                    logger.error(f"Information request {request_id} not found")
                    return False, None

            # Check if already resolved
            if information_request.status == RequestStatus.RESOLVED:
                logger.info(f"Information request {request_id} is already resolved")
                return True, information_request

            # Update the request
            information_request.status = RequestStatus.RESOLVED
            information_request.resolution = resolution
            information_request.resolved_at = datetime.utcnow()
            information_request.resolved_by = current_user_id

            # Add to history
            information_request.updates.append({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user_id,
                "message": f"Request resolved: {resolution}",
                "status": RequestStatus.RESOLVED.value,
            })

            # Update metadata
            information_request.updated_at = datetime.utcnow()
            information_request.updated_by = current_user_id
            information_request.version += 1

            # Save the updated request
            ProjectStorage.write_information_request(project_id, information_request)

            # Log the resolution
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.REQUEST_RESOLVED.value,
                message=f"Resolved information request: {information_request.title}",
                related_entity_id=information_request.request_id,
                metadata={
                    "resolution": resolution,
                    "request_title": information_request.title,
                    "request_priority": information_request.priority.value
                    if hasattr(information_request.priority, "value")
                    else information_request.priority,
                },
            )

            # High priority request has been resolved, could update project info
            # in the future if needed

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="information_request_resolved",
                message=f"Information request resolved: {information_request.title}",
            )

            # Send direct notification to requestor's conversation
            if information_request.conversation_id != str(context.id):
                from semantic_workbench_api_model.workbench_model import (
                    MessageType,
                    NewConversationMessage,
                )

                from .conversation_clients import ConversationClientManager

                try:
                    # Get client for requestor's conversation
                    client = ConversationClientManager.get_conversation_client(
                        context, information_request.conversation_id
                    )

                    # Send notification message
                    await client.send_messages(
                        NewConversationMessage(
                            content=f"Coordinator has resolved your request '{information_request.title}': {resolution}",
                            message_type=MessageType.notice,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Could not send notification to requestor: {e}")

            # Update all project UI inspectors
            await ProjectStorage.refresh_all_project_uis(context, project_id)

            return True, information_request

        except Exception as e:
            logger.exception(f"Error resolving information request: {e}")
            return False, None

    @staticmethod
    async def get_project_log(context: ConversationContext) -> Optional[ProjectLog]:
        """Gets the project log for the current conversation's project."""
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            return None

        return ProjectStorage.read_project_log(project_id)

    @staticmethod
    async def add_log_entry(
        context: ConversationContext,
        entry_type: LogEntryType,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[ProjectLog]]:
        """
        Adds an entry to the project log.

        Args:
            context: Current conversation context
            entry_type: Type of log entry
            message: Log message
            related_entity_id: Optional ID of a related entity
            metadata: Optional additional metadata

        Returns:
            Tuple of (success, project_log)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot add log entry: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id, user_name = await get_current_user(context)
            if not current_user_id:
                logger.error("Cannot add log entry: no user found in conversation")
                return False, None

            # Default user name if none found
            user_name = user_name or "Unknown User"

            # Create the log entry
            entry = LogEntry(
                entry_type=entry_type,
                message=message,
                user_id=current_user_id,
                user_name=user_name,
                related_entity_id=related_entity_id,
                metadata=metadata or {},
            )

            # Get existing log or create new one
            project_log = ProjectStorage.read_project_log(project_id)
            if not project_log:
                project_log = ProjectLog(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    entries=[],
                )

            # Add the entry
            project_log.entries.append(entry)

            # Update metadata
            project_log.updated_at = datetime.utcnow()
            project_log.updated_by = current_user_id
            project_log.version += 1

            # Save the log
            ProjectStorage.write_project_log(project_id, project_log)

            # Notify linked conversations for significant events
            significant_types = [
                LogEntryType.PROJECT_STARTED,
                LogEntryType.PROJECT_COMPLETED,
                LogEntryType.PROJECT_ABORTED,
                LogEntryType.GOAL_COMPLETED,
                LogEntryType.MILESTONE_PASSED,
            ]

            if entry_type in significant_types:
                await ProjectNotifier.notify_project_update(
                    context=context,
                    project_id=project_id,
                    update_type="project_log",
                    message=f"Project update: {message}",
                )

            return True, project_log

        except Exception as e:
            logger.exception(f"Error adding log entry: {e}")
            return False, None

    @staticmethod
    async def get_project_info(context: ConversationContext, project_id: Optional[str] = None) -> Optional[ProjectInfo]:
        """
        Gets the project information including share URL and team conversation details.

        Args:
            context: Current conversation context
            project_id: Optional project ID (if not provided, will be retrieved from context)

        Returns:
            ProjectInfo object or None if not found
        """
        try:
            # Get project ID if not provided
            if not project_id:
                project_id = await ProjectManager.get_project_id(context)
                if not project_id:
                    return None

            # Read project info
            project_info = ProjectStorage.read_project_info(project_id)
            return project_info

        except Exception as e:
            logger.exception(f"Error getting project info: {e}")
            return None

    @staticmethod
    async def get_project_whiteboard(
        context: ConversationContext,
    ) -> Optional[ProjectWhiteboard]:
        """Gets the project whiteboard for the current conversation's project."""
        project_id = await ProjectManager.get_project_id(context)
        if not project_id:
            return None

        return ProjectStorage.read_project_whiteboard(project_id)

    @staticmethod
    async def update_whiteboard(
        context: ConversationContext,
        content: str,
        is_auto_generated: bool = True,
        send_notification: bool = False,  # Add parameter to control notifications
    ) -> Tuple[bool, Optional[ProjectWhiteboard]]:
        """
        Updates the project whiteboard content.

        Args:
            context: Current conversation context
            content: Whiteboard content in markdown format
            is_auto_generated: Whether the content was automatically generated
            send_notification: Whether to send notifications about the update (default: False)

        Returns:
            Tuple of (success, project_kb)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot update whiteboard: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update whiteboard")
            if not current_user_id:
                return False, None

            # Get existing whiteboard or create new one
            whiteboard = ProjectStorage.read_project_whiteboard(project_id)
            is_new = False

            if not whiteboard:
                whiteboard = ProjectWhiteboard(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    content="",
                )
                is_new = True

            # Update the content
            whiteboard.content = content
            whiteboard.is_auto_generated = is_auto_generated

            # Update metadata
            whiteboard.updated_at = datetime.utcnow()
            whiteboard.updated_by = current_user_id
            whiteboard.version += 1

            # Save the whiteboard
            ProjectStorage.write_project_whiteboard(project_id, whiteboard)

            # Log the update
            event_type = LogEntryType.KB_UPDATE
            update_type = "auto-generated" if is_auto_generated else "manual"
            message = f"{'Created' if is_new else 'Updated'} project whiteboard ({update_type})"

            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=event_type.value,
                message=message,
            )

            # Only notify linked conversations if explicitly requested
            # This prevents auto-updates from generating notifications
            if send_notification:
                await ProjectNotifier.notify_project_update(
                    context=context,
                    project_id=project_id,
                    update_type="project_whiteboard",
                    message="Project whiteboard updated",
                )
            else:
                # Just refresh the UI without sending notifications
                await ProjectStorage.refresh_all_project_uis(context, project_id)

            return True, whiteboard

        except Exception as e:
            logger.exception(f"Error updating whiteboard: {e}")
            return False, None

    @staticmethod
    async def auto_update_whiteboard(
        context: ConversationContext,
        chat_history: List[Any],
    ) -> Tuple[bool, Optional[ProjectWhiteboard]]:
        """
        Automatically updates the whiteboard by analyzing chat history.

        This method:
        1. Retrieves recent conversation messages
        2. Sends them to the LLM with a prompt to extract important info
        3. Updates the whiteboard with the extracted content

        Args:
            context: Current conversation context
            chat_history: Recent chat messages to analyze

        Returns:
            Tuple of (success, project_kb)
        """
        logger.error("DEBUG: auto_update_whiteboard called with conversation ID: %s", context.id)
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            logger.error("DEBUG: auto_update_whiteboard found project ID: %s", project_id)
            if not project_id:
                logger.error("Cannot auto-update whiteboard: no project associated with this conversation")
                return False, None

            # Get user information for storage purposes
            current_user_id = await require_current_user(context, "auto-update whiteboard")
            if not current_user_id:
                return False, None

            # Skip if no messages to analyze
            if not chat_history:
                logger.info("No chat history to analyze for whiteboard update")
                return False, None

            # Import necessary model types
            from semantic_workbench_api_model.workbench_model import ParticipantRole

            # Format the chat history for the prompt
            chat_history_text = ""
            for msg in chat_history:
                sender_type = (
                    "User" if msg.sender and msg.sender.participant_role == ParticipantRole.user else "Assistant"
                )
                chat_history_text += f"{sender_type}: {msg.content}\n\n"

            # Get config for the LLM call
            from .chat import assistant_config

            config = await assistant_config.get(context.assistant)

            # Load the whiteboard prompt from text includes
            from .utils import load_text_include

            template_id = context.assistant._template_id

            # Use the appropriate prompt based on the template
            if template_id == "context_transfer":
                whiteboard_prompt_template = load_text_include("context_transfer_whiteboard_prompt.txt")
            else:
                whiteboard_prompt_template = load_text_include("whiteboard_auto_update_prompt.txt")

            # Construct the whiteboard prompt with the chat history
            whiteboard_prompt = f"""
            {whiteboard_prompt_template}

            <CHAT_HISTORY>
            {chat_history_text}
            </CHAT_HISTORY>
            """

            # Import necessary modules for the LLM call
            import openai_client

            # Create a completion with the whiteboard prompt
            async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
                completion = await client.chat.completions.create(
                    model=config.request_config.openai_model,
                    messages=[{"role": "user", "content": whiteboard_prompt}],
                    max_tokens=2500,  # Limiting to 2500 tokens to keep whiteboard content manageable
                )

                # Extract the content from the completion
                content = completion.choices[0].message.content or ""

                # Extract just the whiteboard content
                import re

                whiteboard_content = ""

                # Look for content between <WHITEBOARD> tags
                match = re.search(r"<WHITEBOARD>(.*?)</WHITEBOARD>", content, re.DOTALL)
                if match:
                    whiteboard_content = match.group(1).strip()
                else:
                    # If no tags, use the whole content
                    whiteboard_content = content.strip()

            # Only update if we have content
            if not whiteboard_content:
                logger.info("No content extracted from whiteboard LLM analysis")
                return False, None

            # Update the whiteboard with the extracted content
            # Use send_notification=False to avoid sending notifications for automatic updates
            return await ProjectManager.update_whiteboard(
                context=context,
                content=whiteboard_content,
                is_auto_generated=True,
                send_notification=False,
            )

        except Exception as e:
            logger.exception(f"Error auto-updating whiteboard: {e}")
            return False, None

    @staticmethod
    async def complete_project(
        context: ConversationContext,
        summary: Optional[str] = None,
    ) -> Tuple[bool, Optional[ProjectInfo]]:
        """
        Completes a project and updates the project state.

        Args:
            context: Current conversation context
            summary: Optional summary of project results

        Returns:
            Tuple of (success, project_info)
        """
        try:
            # Get project ID
            project_id = await ProjectManager.get_project_id(context)
            if not project_id:
                logger.error("Cannot complete project: no project associated with this conversation")
                return False, None

            # Get role - only Coordinator can complete a project
            role = await ProjectManager.get_project_role(context)
            if role != ProjectRole.COORDINATOR:
                logger.error("Only Coordinator can complete a project")
                return False, None

            # Update project state to completed
            status_message = summary if summary else "Project completed successfully"
            success, project_info = await ProjectManager.update_project_state(
                context=context,
                state=ProjectState.COMPLETED.value,
                status_message=status_message,
            )

            if not success or not project_info:
                return False, None

            # Add completion entry to the log
            await ProjectStorage.log_project_event(
                context=context,
                project_id=project_id,
                entry_type=LogEntryType.PROJECT_COMPLETED.value,
                message=f"Project completed: {status_message}",
            )

            # Notify linked conversations with emphasis
            await ProjectNotifier.notify_project_update(
                context=context,
                project_id=project_id,
                update_type="project_completed",
                message=f"🎉 PROJECT COMPLETED: {status_message}",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error completing project: {e}")
            return False, None
