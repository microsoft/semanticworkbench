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
    KnowledgePackageLog,
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

        # Store shared conversation info in KnowledgePackage
        knowledge_package = ShareStorage.read_share(share_id)
        if knowledge_package:
            knowledge_package.shared_conversation_id = str(conversation.id)
            knowledge_package.share_url = share_url
            knowledge_package.updated_at = datetime.utcnow()
            ShareStorage.write_share(share_id, knowledge_package)
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
        4. Creates empty project data structures (brief, knowledge digest, etc.)
        5. Logs the project creation event

        After creating a project, the Coordinator should proceed to create a project brief
        with specific learning objectives and success criteria.

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

        # Create and save the initial knowledge package
        knowledge_package = KnowledgePackage(
            share_id=share_id,
            coordinator_conversation_id=str(context.id),
            brief=None,
            digest=None,
        )

        # Save the knowledge package
        ShareStorage.write_share(share_id, knowledge_package)
        logger.debug(f"Created and saved knowledge package: {knowledge_package}")

        # Associate the conversation with the project
        logger.debug(f"Associating conversation {context.id} with project {share_id}")
        await ConversationKnowledgePackageManager.associate_conversation_with_share(context, share_id)

        # No need to set conversation role in project storage, as we use metadata
        logger.debug(f"Conversation {context.id} is Coordinator for project {share_id}")

        # Note: Conversation linking is now handled via JSON data, no directory needed

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
        project = ShareStorage.read_share(share_id)
        if project:
            # Load the separate log file if not already loaded
            if not project.log:
                project.log = ShareStorage.read_share_log(share_id)
        else:
            # Create a new package if it doesn't exist, but this should be rare in get_share
            return None
        return project

    @staticmethod
    async def update_share_state(
        context: ConversationContext,
        status_message: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
        """
        Updates the project status message.

        Args:
            context: Current conversation context
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
            if status_message:
                project_info.transfer_notes = status_message

            # Update metadata
            project_info.updated_at = datetime.utcnow()

            # Save the project info
            ShareStorage.write_share_info(share_id, project_info)

            # Log the update
            event_type = LogEntryType.STATUS_CHANGED
            message = "Updated project status"
            if status_message:
                message += f": {status_message}"

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=event_type.value,
                message=message,
                metadata={
                    "status_message": status_message,
                },
            )

            # Notify linked conversations
            await ProjectNotifier.notify_project_update(
                context=context,
                share_id=share_id,
                update_type="project_state",
                message="KnowledgePackage status updated",
            )

            return True, project_info

        except Exception as e:
            logger.exception(f"Error updating project state: {e}")
            return False, None

    @staticmethod
    async def get_share_info(
        context: ConversationContext, share_id: Optional[str] = None
    ) -> Optional[KnowledgePackage]:
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
        progress: Optional[int] = None,
        status_message: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> Optional[KnowledgePackage]:
        """
        Updates the project info with progress, status message, and next actions.

        Args:
            context: Current conversation context
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
        message = "Updated project status"
        if progress is not None:
            message += f" ({progress}% complete)"
        if status_message:
            message += f": {status_message}"

        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=event_type.value,
            message=message,
            metadata={
                "status_message": status_message,
                "progress": progress,
            },
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="project_info",
            message="KnowledgePackage status updated",
        )

        return project_info

    @staticmethod
    async def get_knowledge_brief(context: ConversationContext) -> Optional[KnowledgeBrief]:
        """
        Gets the brief for the current conversation's knowledge share.

        The brief contains the core information about the knowledge share:
        name, description, learning objectives, and success criteria. This is the central
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

        return ShareStorage.read_knowledge_brief(share_id)

    @staticmethod
    async def update_knowledge_brief(
        context: ConversationContext,
        title: str,
        description: str,
        timeline: Optional[str] = None,
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
            content=description,
            timeline=timeline,
            created_by=current_user_id,
            updated_by=current_user_id,
            conversation_id=str(context.id),
        )

        # Save the brief
        ShareStorage.write_knowledge_brief(share_id, brief)

        # Check if this is a creation or an update
        existing_brief = ShareStorage.read_knowledge_brief(share_id)
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
            priority: Priority of the learning objective (default: 1)

        Returns:
            The created LearningObjective if successful, None otherwise
        """
        # Get project ID
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot add learning objective: no project associated with this conversation")
            return None

        # Get user information
        current_user_id = await require_current_user(context, "add learning objective")
        if not current_user_id:
            return None

        # Create success criteria objects if provided
        criterion_objects = []
        if outcomes:
            for criterion in outcomes:
                criterion_objects.append(LearningOutcome(description=criterion))

        # Create the new learning objective
        new_learning_objective = LearningObjective(
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
                share_id=share_id,
                brief=None,
                learning_objectives=[new_learning_objective],
                digest=None,
                requests=[],
                log=None,
            )
        else:
            # Add the learning objective to the existing project
            project.learning_objectives.append(new_learning_objective)

        # Save the updated project
        ShareStorage.write_share(share_id, project)

        # Log the learning objective addition
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_ADDED.value,
            message=f"Added learning objective: {objective_name}",
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="learning objective",
            message=f"learning objective added: {objective_name}",
        )

        return new_learning_objective

    @staticmethod
    async def delete_learning_objective(
        context: ConversationContext,
        objective_index: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Deletes a learning objective from the project.

        Args:
            context: Current conversation context
            objective_index: The index of the learning objective to delete (0-based)

        Returns:
            Tuple of (success, objective_name_or_error_message)
        """
        # Get project ID
        share_id = await KnowledgeTransferManager.get_share_id(context)
        if not share_id:
            logger.error("Cannot delete learning objective: no project associated with this conversation")
            return False, "No project associated with this conversation."

        # Get user information
        current_user_id = await require_current_user(context, "delete learning objective")
        if not current_user_id:
            return False, "Could not identify current user."

        # Get the existing project
        project = ShareStorage.read_share(share_id)
        if not project or not project.learning_objectives:
            return False, "No project learning objectives found."

        # Validate index
        if objective_index < 0 or objective_index >= len(project.learning_objectives):
            return (
                False,
                f"Invalid learning objective index {objective_index}. Valid indexes are 0 to {len(project.learning_objectives) - 1}. There are {len(project.learning_objectives)} learning objectives.",
            )

        # Get the learning objective to delete
        learning_objective = project.learning_objectives[objective_index]
        learning_objective_name = learning_objective.name

        # Remove the learning objective from the list
        project.learning_objectives.pop(objective_index)

        # Save the updated project
        ShareStorage.write_share(share_id, project)

        # Log the learning objective deletion
        await ShareStorage.log_share_event(
            context=context,
            share_id=share_id,
            entry_type=LogEntryType.LEARNING_OBJECTIVE_DELETED.value,
            message=f"Deleted learning objective: {learning_objective_name}",
        )

        # Notify linked conversations
        await ProjectNotifier.notify_project_update(
            context=context,
            share_id=share_id,
            update_type="learning objective",
            message=f"learning objective deleted: {learning_objective_name}",
        )

        # Update project info with new criteria counts
        project_info = ShareStorage.read_share_info(share_id)
        if project_info:
            # Count all completed criteria
            completed_criteria = 0
            total_criteria = 0

            # Get the updated project to access learning objectives
            updated_project = ShareStorage.read_share(share_id)
            if updated_project:
                # Use the new overall completion calculation
                completed_criteria, total_criteria = updated_project.get_overall_completion()

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

        return True, learning_objective_name

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

        # Get the project which contains learning objectives and success criteria
        project = ShareStorage.read_share(share_id)
        if not project:
            return []

        objectives = project.learning_objectives
        outcomes = []
        for objective in objectives:
            # Add success criteria from each learning objective
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
        related_objective_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[InformationRequest]]:
        """
        Creates a new information request.

        Args:
            context: Current conversation context
            title: Title of the request
            description: Description of the request
            priority: Priority level
            related_objective_ids: Optional list of related learning objective IDs

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
                related_objective_ids=related_objective_ids or [],
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
                logger.error("Cannot update knowledge digest: no project associated with this conversation")
                return False, None

            # Get user information
            current_user_id = await require_current_user(context, "update knowledge digest")
            if not current_user_id:
                return False, None

            # Get existing knowledge digest or create new one
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

            # Save the knowledge digest
            ShareStorage.write_knowledge_digest(share_id, digest)

            # Log the update
            event_type = LogEntryType.KNOWLEDGE_DIGEST_UPDATE
            update_type = "auto-generated" if is_auto_generated else "manual"
            message = f"{'Created' if is_new else 'Updated'} knowledge digest ({update_type})"

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
                    update_type="knowledge_digest",
                    message="KnowledgePackage knowledge digest updated",
                )
            else:
                # Just refresh the UI without sending notifications
                await ShareStorage.refresh_all_share_uis(context, share_id)

            return True, digest

        except Exception as e:
            logger.exception(f"Error updating knowledge digest: {e}")
            return False, None

    @staticmethod
    async def auto_update_knowledge_digest(
        context: ConversationContext,
    ) -> Tuple[bool, Optional[KnowledgeDigest]]:
        """
        Automatically updates the knowledge digest by analyzing chat history.

        This method:
        1. Retrieves recent conversation messages
        2. Sends them to the LLM with a prompt to extract important info
        3. Updates the knowledge digest with the extracted content

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
                logger.error("Cannot auto-update knowledge digest: no project associated with this conversation")
                return False, None

            # Get user information for storage purposes
            current_user_id = await require_current_user(context, "auto-update knowledge digest")
            if not current_user_id:
                return False, None

            # Skip if no messages to analyze
            if not chat_history:
                logger.warning("No chat history to analyze for knowledge digest update")
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

            # Construct the knowledge digest prompt with the chat history
            digest_prompt = f"""
            {config.prompt_config.knowledge_digest_prompt}

            <CHAT_HISTORY>
            {chat_history_text}
            </CHAT_HISTORY>
            """

            # Create a completion with the knowledge digest prompt
            async with openai_client.create_client(config.service_config, api_version="2024-06-01") as client:
                completion = await client.chat.completions.create(
                    model=config.request_config.openai_model,
                    messages=[{"role": "user", "content": digest_prompt}],
                    max_tokens=2500,  # Limiting to 2500 tokens to keep digest content manageable
                )

                # Extract the content from the completion
                content = completion.choices[0].message.content or ""

                # Extract just the knowledge digest content
                digest_content = ""

                # Look for content between <KNOWLEDGE_DIGEST> tags
                match = re.search(r"<KNOWLEDGE_DIGEST>(.*?)</KNOWLEDGE_DIGEST>", content, re.DOTALL)
                if match:
                    digest_content = match.group(1).strip()
                else:
                    # If no tags, use the whole content
                    digest_content = content.strip()

            # Only update if we have content
            if not digest_content:
                logger.warning("No content extracted from knowledge digest LLM analysis")
                return False, None

            # Update the knowledge digest with the extracted content
            # Use send_notification=False to avoid sending notifications for automatic updates
            return await KnowledgeTransferManager.update_knowledge_digest(
                context=context,
                content=digest_content,
                is_auto_generated=True,
                send_notification=False,
            )

        except Exception as e:
            logger.exception(f"Error auto-updating knowledge digest: {e}")
            return False, None

    @staticmethod
    async def complete_project(
        context: ConversationContext,
        summary: Optional[str] = None,
    ) -> Tuple[bool, Optional[KnowledgePackage]]:
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

    @staticmethod
    async def get_coordinator_next_action_suggestion(context: ConversationContext) -> Optional[str]:
        """
        Generate next action suggestions for the coordinator based on the knowledge transfer state.

        This output is passed to the assistant and helps guide the conversation toward completing or improving
        the knowledge package in a helpful, structured way.

        Returns:
            A user-facing suggestion string, or None if no suggestion is needed.
        """
        try:
            share_id = await KnowledgeTransferManager.get_share_id(context)
            if not share_id:
                logger.warning("No share ID found for this conversation")
                return None

            package = ShareStorage.read_share(share_id)
            if not package:
                return None

            brief = ShareStorage.read_knowledge_brief(share_id)
            requests = ShareStorage.get_all_information_requests(share_id)
            active_requests = [r for r in requests if r.status == RequestStatus.NEW]

            # 1. Unresolved requests come first
            if active_requests:
                request = active_requests[0]
                return f'There are {len(active_requests)} unanswered questions from team members. One of them is: "{request.title}" Let\'s work on answering it.'

            # 2. Audience not yet defined
            if not package.audience:
                return "Let's start by defining who your audience is. Who is this knowledge for, and what's their background?"

            # 3. Knowledge not yet organized
            if not package.knowledge_organized:
                return "Next, let's organize your knowledge. Upload any relevant files or describe the knowledge you want to transfer. When you're ready, I can mark the knowledge as organized."

            # 4. Brief not yet written
            if not brief:
                return "Your package needs a short introduction that will orient your team. Let's write a knowledge brief next."

            # 5. If intended to have outcomes but none defined yet
            if package.is_intended_to_accomplish_outcomes and not package.learning_objectives:
                return (
                    "Would you like your team to achieve any specific outcomes? If so, let's define some learning objectives. "
                    "If not, you can mark this package as 'exploratory' instead."
                )

            # 6. Objectives exist, but missing outcomes
            if package.is_intended_to_accomplish_outcomes:
                incomplete_objectives = [obj for obj in package.learning_objectives if not obj.learning_outcomes]
                if incomplete_objectives:
                    name = incomplete_objectives[0].name
                    return f"The learning objective “{name}” doesn't have any outcomes yet. Let's define what your team should accomplish to meet it."

            # 7. Ready for transfer but not yet shared
            if package.is_ready_for_transfer() and not package.is_actively_sharing():
                return "Your knowledge package is ready to share. Would you like to create a message and generate the invitation link?"

            # 8. Actively sharing - monitor and support ongoing transfer
            if package.is_actively_sharing():
                if package.is_intended_to_accomplish_outcomes and not package._is_transfer_complete():
                    team_count = len(package.team_conversations)
                    return f"Great! Your knowledge is being shared with {team_count} team member{'s' if team_count != 1 else ''}. You can continue improving the package or respond to information requests as they come in."
                else:
                    return "Your knowledge transfer is in progress. You can continue improving the package or respond to information requests as they come in."

            # 9. Default: General support
            return "Your package is available. You can continue improving it or respond to new information requests as they come in."

        except Exception as e:
            logger.exception(f"Error generating next action suggestion: {e}")
            return None
