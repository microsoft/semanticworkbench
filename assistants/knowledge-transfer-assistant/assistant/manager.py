"""
KnowledgePackage management logic for working with project data.

This module provides the core business logic for working with project data
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import openai_client
from semantic_workbench_api_model.workbench_model import (
    ConversationPermission,
    MessageType,
    NewConversation,
    NewConversationMessage,
    NewConversationShare,
    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .config import assistant_config
from .conversation_clients import ConversationClientManager
from .conversation_share_link import ConversationKnowledgePackageManager
from .data import (
    InformationRequest,
    KnowledgeBrief,
    KnowledgeDigest,
    KnowledgePackage,
    KnowledgePackageInfo,
    KnowledgePackageLog,
    KnowledgeTransferState,
    LearningObjective,
    LearningOutcome,
    LogEntryType,
    RequestPriority,
    RequestStatus,
)
from .logging import logger
from .notifications import ProjectNotifier
from .storage import ShareStorage, ShareStorageManager
from .storage_models import ConversationRole
from .utils import get_current_user, require_current_user


class KnowledgeTransferManager:
    """
    Manages the creation, modification, and lifecycle of knowledge transfer packages.

    The KnowledgeTransferManager provides a centralized set of operations for working with project data.
    It handles all the core business logic for interacting with projects, ensuring that
    operations are performed consistently and following the proper rules and constraints.

    This class implements the primary interface for both Coordinators and team members to interact
    with project entities like briefs, information requests, and knowledge bases. It abstracts
    away the storage details and provides a clean API for project operations.

    All methods are implemented as static methods to facilitate easy calling from
    different parts of the codebase without requiring instance creation.
    """

    @staticmethod
    async def create_shareable_team_conversation(context: ConversationContext, share_id: str) -> str:
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
            share_id: ID of the project

        Returns:
            share_url: URL for joining a team conversation
        """

        # Get the current user ID to set as owner
        user_id, _ = await get_current_user(context)
        if not user_id:
            raise ValueError("Cannot create team conversation: no user found")

        new_conversation = NewConversation(
            metadata={
                "is_team_conversation": True,
                "share_id": share_id,
                "setup_complete": True,
                "project_role": "team",
                "assistant_mode": "team",
            },
        )
        client = context._conversations_client
        conversation = await client.create_conversation_with_owner(new_conversation=new_conversation, owner_id=user_id)

        if not conversation or not conversation.id:
            raise ValueError("Failed to create team conversation")

        new_share = NewConversationShare(
            conversation_id=conversation.id,
            label="Join Team Conversation",
            conversation_permission=ConversationPermission.read,
            metadata={
                "share_id": share_id,
                "is_team_conversation": True,
                "showDuplicateAction": True,
                "show_duplicate_action": True,
            },
        )
        share = await context._conversations_client.create_conversation_share_with_owner(
            new_conversation_share=new_share, owner_id=user_id
        )

        share_url = f"/conversation-share/{share.id}/redeem"

        # Store team conversation info in KnowledgePackageInfo
        project_info = ShareStorage.read_share_info(share_id)
        if project_info:
            project_info.team_conversation_id = str(conversation.id)
            project_info.share_url = share_url
            project_info.updated_at = datetime.utcnow()
            ShareStorage.write_share_info(share_id, project_info)
        else:
            raise ValueError(f"KnowledgePackage info not found for project ID: {share_id}")

        return share_url

    @staticmethod
    async def create_share(context: ConversationContext) -> str:
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
            Tuple of (success, share_id) where:
            - success: Boolean indicating if the creation was successful
            - share_id: If successful, the UUID of the newly created project
        """

        # Generate a unique project ID
        share_id = str(uuid.uuid4())

        # Create the project directory structure first
        project_dir = ShareStorageManager.get_share_dir(share_id)
        logger.debug(f"Created project directory: {project_dir}")

        # Create and save the initial project info
        project_info = KnowledgePackageInfo(share_id=share_id, coordinator_conversation_id=str(context.id))

        # Save the project info
        ShareStorage.write_share_info(share_id, project_info)
        logger.debug(f"Created and saved project info: {project_info}")

        # Associate the conversation with the project
        logger.debug(f"Associating conversation {context.id} with project {share_id}")
        await ConversationKnowledgePackageManager.associate_conversation_with_share(context, share_id)

        # No need to set conversation role in project storage, as we use metadata
        logger.debug(f"Conversation {context.id} is Coordinator for project {share_id}")

        # Ensure linked_conversations directory exists
        linked_dir = ShareStorageManager.get_linked_conversations_dir(share_id)
        logger.debug(f"Ensured linked_conversations directory exists: {linked_dir}")

        return share_id

    @staticmethod
    async def join_share(
        context: ConversationContext,
        share_id: str,
        role: ConversationRole = ConversationRole.TEAM,
    ) -> bool:
        """
        Joins an existing project.

        Args:
            context: Current conversation context
            share_id: ID of the project to join
            role: Role for this conversation (COORDINATOR or TEAM)

        Returns:
            True if joined successfully, False otherwise
        """
        try:
            # Check if project exists
            if not ShareStorageManager.share_exists(share_id):
                logger.error(f"Cannot join project: project {share_id} does not exist")
                return False

            # Associate the conversation with the project
            await ConversationKnowledgePackageManager.associate_conversation_with_share(context, share_id)

            # Role is set in metadata, not in storage

            logger.info(f"Joined project {share_id} as {role.value}")
            return True

        except Exception as e:
            logger.exception(f"Error joining project: {e}")
            return False

    @staticmethod
    async def get_share_id(context: ConversationContext) -> Optional[str]:
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
        return await ConversationKnowledgePackageManager.get_associated_share_id(context)

    @staticmethod
    async def get_share_role(context: ConversationContext) -> Optional[ConversationRole]:
        """
        Gets the role of the current conversation in its project.

        Each conversation participating in a project has a specific role:
        - COORDINATOR: The primary conversation that created and manages the project
        - TEAM: Conversations where team members are carrying out the project tasks

        This method examines the conversation metadata to determine the role
        of the current conversation in the project. The role is stored in the
        conversation metadata as "project_role".

        Args:
            context: Current conversation context

        Returns:
            The role (KnowledgePackageRole.COORDINATOR or KnowledgePackageRole.TEAM) if the conversation
            is part of a project, None otherwise
        """
        try:
            conversation = await context.get_conversation()
            metadata = conversation.metadata or {}
            role_str = metadata.get("project_role", "coordinator")

            if role_str == "team":
                return ConversationRole.TEAM
            elif role_str == "coordinator":
                return ConversationRole.COORDINATOR
            else:
                return None
        except Exception as e:
            logger.exception(f"Error detecting project role: {e}")
            # Default to None if we can't determine
            return None

    @staticmethod
    async def get_share_log(context: ConversationContext) -> Optional[KnowledgePackageLog]:
        """Gets the project log for the current conversation's project."""
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return None

        return ShareStorage.read_share_log(share_id)

    @staticmethod
    async def get_share(context: ConversationContext) -> Optional[KnowledgePackage]:
        """Gets the project information for the current conversation's project."""
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return None
        project = KnowledgePackage(
            info=ShareStorage.read_share_info(share_id),
            brief=ShareStorage.read_share_brief(share_id),
            learning_objectives=[],  # TODO: Add storage method for learning objectives
            digest=ShareStorage.read_knowledge_digest(share_id),
            requests=ShareStorage.get_all_information_requests(share_id),
            log=ShareStorage.read_share_log(share_id),
        )
        return project

    @staticmethod
    async def get_share_state(
        context: ConversationContext,
    ) -> Optional[KnowledgeTransferState]:
        """Gets the project state for the current conversation's project."""
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return None

        # Get the project info which contains state information
        project_info = ShareStorage.read_share_info(share_id)
        if not project_info:
            return None

        return project_info.transfer_state

    @staticmethod
    async def update_share_state(
        context: ConversationContext,
        state: Optional[str] = None,
        status_message: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackageInfo]]:
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
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot update project state: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update project state")
            if not current_user_id:
                return False, None

            # Get existing project info
            project_info = ShareStorage.read_share_info(share_id)
            if not project_info:
                logger.error(f"Cannot update project state: no project info found for {share_id}")
                return False, None

            # Apply updates
            if state:
                project_info.transfer_state = KnowledgeTransferState(state)

            if status_message:
                project_info.transfer_notes = status_message

            # Update metadata
            project_info.updated_at = datetime.utcnow()

            # Save the project info
            ShareStorage.write_share_info(share_id, project_info)

            # Log the update
            event_type = LogEntryType.STATUS_CHANGED
            message = f"Updated project state to {project_info.transfer_state.value}"

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=event_type.value,
                message=message,
                metadata={
                    "state": project_info.transfer_state.value,
                    "status_message": status_message,
                },
            )

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="project_state",
                message=f"KnowledgePackage state updated: {project_info.transfer_state.value}",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error updating project state: {e}")
            return False, None

    @staticmethod
    async def get_share_info(
        context: ConversationContext, share_id: Optional[str] = None
    ) -> Optional[KnowledgePackageInfo]:
        """
        Gets the project information including share URL and team conversation details.

        Args:
            context: Current conversation context
            share_id: Optional project ID (if not provided, will be retrieved from context)

        Returns:
            KnowledgePackageInfo object or None if not found
        """
        try:
            # Get project ID if not provided
            if not share_id:
                share_id = await KnowledgeTransferManager.get_share_id(context)
                if not share_id:
                    return None

            # Read project info
            project_info = ShareStorage.read_share_info(share_id)
            return project_info

        except Exception as e:
            logger.exception(f"Error getting project info: {e}")
            return None

    @staticmethod
    async def update_share_info(
        context: ConversationContext,
        state: Optional[str] = None,
        progress: Optional[int] = None,
        status_message: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> Optional[KnowledgePackageInfo]:
        """
        Updates the project info with state, progress, status message, and next actions.

        Args:
            context: Current conversation context
            state: Optional project state
            progress: Optional progress percentage (0-100)
            status_message: Optional status message
            next_actions: Optional list of next actions

        Returns:
            Tuple of (success, project_info)
        """
        # Get project ID
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot update project info: no project associated with this conversation")
            return None

        # Get user information
        current_user_id = await require_current_user(context, "update project info")
        if not current_user_id:
            return None

        # Get existing project info
        project_info = ShareStorage.read_share_info(share_id)
        if not project_info:
            logger.error(f"Cannot update project info: no project info found for {share_id}")
            return None

        # Apply updates
        if state:
            project_info.transfer_state = KnowledgeTransferState(state)

        if status_message:
            project_info.transfer_notes = status_message

        if progress is not None:
            project_info.completion_percentage = progress

        if next_actions:
            project_info.next_learning_actions = next_actions

        # Update metadata
        project_info.updated_at = datetime.utcnow()
        project_info.updated_by = current_user_id

        # Increment version if it exists
        if hasattr(project_info, "version"):
            project_info.version += 1

        # Save the project info
        ShareStorage.write_share_info(share_id, project_info)

        # Log the update
        event_type = LogEntryType.STATUS_CHANGED
        message = f"Updated project status to {project_info.transfer_state.value}"
        if progress is not None:
            message += f" ({progress}% complete)"

        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=event_type.value,
            message=message,
            metadata={
                "state": project_info.transfer_state.value,
                "status_message": status_message,
                "progress": progress,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="project_info",
            message=f"KnowledgePackage status updated: {project_info.transfer_state.value}",
        )

        return project_info

    @staticmethod
    async def get_knowledge_brief(context: ConversationContext) -> Optional[KnowledgeBrief]:
        """
        Gets the brief for the current conversation's knowledge share.

        The brief contains the core information about the knowledge share:
        name, description, goals, and success criteria. This is the central
        document that defines what the knowledge share is trying to accomplish.

        Args:
            context: Current conversation context

        Returns:
            The KnowledgeBrief object if found, None if the conversation is not
            part of a knowledge share or if no brief has been created yet
        """
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return None

        return ShareStorage.read_share_brief(share_id)

    @staticmethod
    async def update_knowledge_brief(
        context: ConversationContext,
        title: str,
        description: str,
        timeline: Optional[str] = None,
        additional_context: Optional[str] = None,
        send_notification: bool = True,
    ) -> Optional[KnowledgeBrief]:
        """
        Creates or updates a knowledge brief for the current knowledge share.

        The brief is the primary document that defines the knowledge share for team members.

        Args:
            context: A reference to the conversation context object
            title: Short, descriptive name for the knowledge share
            description: Comprehensive description of the knowledge share's purpose
            timeline: Optional information about timeline/deadlines
            additional_context: Optional additional relevant information
            send_notification: Whether to send a notification about the brief update (default: True)

        Returns:
            The updated KnowledgeBrief object if successful, None otherwise
        """
        # Get project ID
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot update brief: no project associated with this conversation")
            return
        # Get user information
        current_user_id = await require_current_user(context, "update brief")
        if not current_user_id:
            return

        # Create the project brief
        brief = KnowledgeBrief(
            title=title,
            description=description,
            timeline=timeline,
            additional_context=additional_context,
            created_by=current_user_id,
            updated_by=current_user_id,
            conversation_id=str(context.id),
        )

        # Save the brief
        ShareStorage.write_share_brief(share_id, brief)

        # Check if this is a creation or an update
        existing_brief = ShareStorage.read_share_brief(share_id)
        if existing_brief:
            # This is an update
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Updated brief: {title}",
            )
        else:
            # This is a creation
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.BRIEFING_CREATED.value,
                message=f"Created brief: {title}",
            )

        # Only notify if send_notification is True
        if send_notification:
            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="brief",
                message=f"Brief created: {title}",
            )

        return brief

    @staticmethod
    async def add_learning_objective(
        context: ConversationContext,
        objective_name: str,
        description: str,
        outcomes: Optional[List[str]] = None,
        priority: int = 1,
    ) -> Optional[LearningObjective]:
        """
        Adds a learning objective to the project.

        Args:
            context: Current conversation context
            objective_name: Name of the learning objective
            description: Description of the learning objective
            outcomes: List of learning outcome strings (optional)
            priority: Priority of the goal (default: 1)

        Returns:
            The created LearningObjective if successful, None otherwise
        """
        # Get project ID
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot add goal: no project associated with this conversation")
            return None

        # Get user information
        current_user_id = await require_current_user(context, "add goal")
        if not current_user_id:
            return None

        # Create success criteria objects if provided
        criterion_objects = []
        if outcomes:
            for criterion in outcomes:
                criterion_objects.append(LearningOutcome(description=criterion))

        # Create the new goal
        new_goal = LearningObjective(
            name=objective_name,
            description=description,
            priority=priority,
            learning_outcomes=criterion_objects,
        )

        # Get the existing project
        project = ShareStorage.read_share(share_id)
        if not project:
            # Create a new project if it doesn't exist
            project = KnowledgePackage(
                info=None,
                brief=None,
                learning_objectives=[new_goal],
                digest=None,
                requests=[],
                log=None,
            )
        else:
            # Add the goal to the existing project
            project.learning_objectives.append(new_goal)

        # Save the updated project
        ShareStorage.write_share(share_id, project)

        # Log the goal addition
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.GOAL_ADDED.value,
            message=f"Added goal: {objective_name}",
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="goal",
            message=f"Goal added: {objective_name}",
        )

        return new_goal

    @staticmethod
    async def delete_learning_objective(
        context: ConversationContext,
        objective_index: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Deletes a goal from the project.

        Args:
            context: Current conversation context
            objective_index: The index of the learning objective to delete (0-based)

        Returns:
            Tuple of (success, objective_name_or_error_message)
        """
        # Get project ID
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot delete goal: no project associated with this conversation")
            return False, "No project associated with this conversation."

        # Get user information
        current_user_id = await require_current_user(context, "delete goal")
        if not current_user_id:
            return False, "Could not identify current user."

        # Get the existing project
        project = ShareStorage.read_share(share_id)
        if not project or not project.learning_objectives:
            return False, "No project goals found."

        # Validate index
        if objective_index < 0 or objective_index >= len(project.learning_objectives):
            return (
                False,
                f"Invalid goal index {objective_index}. Valid indexes are 0 to {len(project.learning_objectives) - 1}. There are {len(project.learning_objectives)} goals.",
            )

        # Get the goal to delete
        goal = project.learning_objectives[objective_index]
        goal_name = goal.name

        # Remove the goal from the list
        project.learning_objectives.pop(objective_index)

        # Save the updated project
        ShareStorage.write_share(share_id, project)

        # Log the goal deletion
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.GOAL_DELETED.value,
            message=f"Deleted goal: {goal_name}",
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="goal",
            message=f"Goal deleted: {goal_name}",
        )

        # Update project info with new criteria counts
        project_info = ShareStorage.read_share_info(share_id)
        if project_info:
            # Count all completed criteria
            completed_criteria = 0
            total_criteria = 0

            # Get the updated project to access goals
            updated_project = ShareStorage.read_share(share_id)
            if updated_project and updated_project.learning_objectives:
                for g in updated_project.learning_objectives:
                    total_criteria += len(g.learning_outcomes)
                    completed_criteria += sum(1 for c in g.learning_outcomes if c.achieved)

            # Update project info with criteria stats
            # Note: achieved_criteria not in KnowledgePackageInfo model
            # Note: total_criteria not in KnowledgePackageInfo model

            # Calculate progress percentage
            if total_criteria > 0:
                project_info.completion_percentage = int((completed_criteria / total_criteria) * 100)
            else:
                project_info.completion_percentage = 0

            # Update metadata
            project_info.updated_at = datetime.utcnow()
            project_info.updated_by = current_user_id
            project_info.version += 1

            # Save the updated project info
            ShareStorage.write_share_info(share_id, project_info)

        # Update all project UI inspectors
        await ShareStorage.refresh_all_share_uis(context, share_id)

        return True, goal_name

    @staticmethod
    async def get_learning_outcomes(context: ConversationContext) -> List[LearningOutcome]:
        """
        Gets the learning outcomes for the current knowledge share.

        Args:
            context: Current conversation context
            completed_only: If True, only return completed criteria

        Returns:
            List of LearningOutcome objects
        """
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return []

        # Get the project which contains goals and success criteria
        project = ShareStorage.read_share(share_id)
        if not project:
            return []

        objectives = project.learning_objectives
        outcomes = []
        for objective in objectives:
            # Add success criteria from each goal
            outcomes.extend(objective.learning_outcomes)

        return outcomes

    @staticmethod
    async def get_information_requests(
        context: ConversationContext,
    ) -> List[InformationRequest]:
        """Gets all information requests for the current conversation's project."""
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return []

        return ShareStorage.get_all_information_requests(share_id)

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
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
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
            ShareStorage.write_information_request(share_id, information_request)

            # Log the creation
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
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
                share_id=share_id,
                update_type="information_request",
                message=f"New information request: {title} (Priority: {priority.value})",
            )

            # Update all project UI inspectors
            await ShareStorage.refresh_all_share_uis(context, share_id)

            return True, information_request

        except Exception as e:
            logger.exception(f"Error creating information request: {e}")
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
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot resolve information request: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "resolve information request")
            if not current_user_id:
                return False, None

            # Get the information request
            information_request = ShareStorage.read_information_request(share_id, request_id)
            if not information_request:
                # Try to find it in all requests
                all_requests = ShareStorage.get_all_information_requests(share_id)
                for request in all_requests:
                    if request.request_id == request_id:
                        information_request = request
                        break

                if not information_request:
                    logger.error(f"Information request {request_id} not found")
                    return False, None

            # Check if already resolved
            if information_request.status == RequestStatus.RESOLVED:
                logger.warning(f"Information request {request_id} is already resolved")
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
            ShareStorage.write_information_request(share_id, information_request)

            # Log the resolution
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
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
                share_id=share_id,
                update_type="information_request_resolved",
                message=f"Information request resolved: {information_request.title}",
            )

            # Send direct notification to requestor's conversation
            if information_request.conversation_id != str(context.id):
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
            await ShareStorage.refresh_all_share_uis(context, share_id)

            return True, information_request

        except Exception as e:
            logger.exception(f"Error resolving information request: {e}")
            return False, None

    @staticmethod
    async def get_knowledge_digest(
        context: ConversationContext,
    ) -> Optional[KnowledgeDigest]:
        """Gets the knowledge digest for the current conversation's knowledge share."""
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            return None

        return ShareStorage.read_knowledge_digest(share_id)

    @staticmethod
    async def update_knowledge_digest(
        context: ConversationContext,
        content: str,
        is_auto_generated: bool = True,
        send_notification: bool = False,  # Add parameter to control notifications
    ) -> Tuple[bool, Optional[KnowledgeDigest]]:
        """
        Updates the knowledge digest content.

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
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot update whiteboard: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update whiteboard")
            if not current_user_id:
                return False, None

            # Get existing whiteboard or create new one
            digest = ShareStorage.read_knowledge_digest(share_id)
            is_new = False

            if not digest:
                digest = KnowledgeDigest(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    content="",
                )
                is_new = True

            # Update the content
            digest.content = content
            digest.is_auto_generated = is_auto_generated

            # Update metadata
            digest.updated_at = datetime.utcnow()
            digest.updated_by = current_user_id
            digest.version += 1

            # Save the whiteboard
            ShareStorage.write_share_whiteboard(share_id, digest)

            # Log the update
            event_type = LogEntryType.KB_UPDATE
            update_type = "auto-generated" if is_auto_generated else "manual"
            message = f"{'Created' if is_new else 'Updated'} project whiteboard ({update_type})"

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=event_type.value,
                message=message,
            )

            # Only notify linked conversations if explicitly requested
            # This prevents auto-updates from generating notifications
            if send_notification:
                await ProjectNotifier.notify_project_update(
                    context=context,
                    share_id=share_id,
                    update_type="project_whiteboard",
                    message="KnowledgePackage whiteboard updated",
                )
            else:
                # Just refresh the UI without sending notifications
                await ShareStorage.refresh_all_share_uis(context, share_id)

            return True, digest

        except Exception as e:
            logger.exception(f"Error updating whiteboard: {e}")
            return False, None

    @staticmethod
    async def auto_update_knowledge_digest(
        context: ConversationContext,
    ) -> Tuple[bool, Optional[KnowledgeDigest]]:
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
        try:
            messages = await context.get_messages()
            chat_history = messages.messages

            # Get project ID
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot auto-update whiteboard: no project associated with this conversation")
                return False, None

            # Get user information for storage purposes
            current_user_id = await require_current_user(context, "auto-update whiteboard")
            if not current_user_id:
                return False, None

            # Skip if no messages to analyze
            if not chat_history:
                logger.warning("No chat history to analyze for whiteboard update")
                return False, None

            # Format the chat history for the prompt
            chat_history_text = ""
            for msg in chat_history:
                sender_type = (
                    "User" if msg.sender and msg.sender.participant_role == ParticipantRole.user else "Assistant"
                )
                chat_history_text += f"{sender_type}: {msg.content}\n\n"

            # Get config for the LLM call
            config = await assistant_config.get(context.assistant)

            # Construct the whiteboard prompt with the chat history
            whiteboard_prompt = f"""
            {config.prompt_config.whiteboard_prompt}

            <CHAT_HISTORY>
            {chat_history_text}
            </CHAT_HISTORY>
            """

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
                logger.warning("No content extracted from whiteboard LLM analysis")
                return False, None

            # Update the whiteboard with the extracted content
            # Use send_notification=False to avoid sending notifications for automatic updates
            return await KnowledgeTransferManager.update_knowledge_digest(
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
    ) -> Tuple[bool, Optional[KnowledgePackageInfo]]:
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
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot complete project: no project associated with this conversation")
                return False, None

            # Get role - only Coordinator can complete a project
            role = await KnowledgeTransferManager.get_share_role(context)
            if role != ConversationRole.COORDINATOR:
                logger.error("Only Coordinator can complete a project")
                return False, None

            # Update project state to completed
            status_message = summary if summary else "KnowledgePackage completed successfully"
            success, project_info = await KnowledgeTransferManager.update_share_state(
                context=context,
                state=KnowledgeTransferState.COMPLETED.value,
                status_message=status_message,
            )

            if not success or not project_info:
                return False, None

            # Add completion entry to the log
            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=LogEntryType.SHARE_COMPLETED.value,
                message=f"KnowledgePackage completed: {status_message}",
            )

            # Notify linked conversations with emphasis
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="project_completed",
                message=f"🎉 PROJECT COMPLETED: {status_message}",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error completing project: {e}")
            return False, None
