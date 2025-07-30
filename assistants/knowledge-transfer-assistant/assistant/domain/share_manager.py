"""
Share/Project management operations for Knowledge Transfer Assistant.

Handles creation, joining, and basic share operations.
"""

import uuid
from csv import Error
from datetime import UTC, datetime

from semantic_workbench_api_model.workbench_model import (
    ConversationPermission,
    NewConversation,
    NewConversationShare,
)
from semantic_workbench_assistant.assistant_app import ConversationContext
from semantic_workbench_assistant.storage import read_model, write_model

from assistant.data import (
    ConversationRole,
    ConversationShareInfo,
    CoordinatorConversationMessages,
    KnowledgePackage,
    KnowledgePackageLog,
    TeamConversationInfo,
)
from assistant.errors import NoShareException, NoShareFoundError
from assistant.logging import logger
from assistant.storage import ShareStorage, ShareStorageManager
from assistant.utils import get_current_user


class ShareManager:
    """Manages knowledge share creation, joining, and basic operations."""

    @staticmethod
    async def create_share(context: ConversationContext) -> str:
        """
        Creates a new knowledge share and associates the current conversation with it.

        This is the initial step in knowledge transfer creation. It:
        1. Generates a unique knowledge share ID
        2. Associates the current conversation with that share
        3. Sets the current conversation as Coordinator for the share
        4. Creates empty share data structures (brief, knowledge digest, etc.)
        5. Logs the creation event

        After creating a share, the Coordinator should proceed to create a knowledge brief
        with specific learning objectives and success criteria.

        Args:
            context: Current conversation context containing user/assistant information

        Returns:
            Tuple of (success, share_id) where:
            - success: Boolean indicating if the creation was successful
            - share_id: If successful, the UUID of the newly created share
        """

        share_id = str(uuid.uuid4())

        share_dir = ShareStorageManager.get_share_dir(share_id)
        logger.debug(f"Created share directory: {share_dir}")

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

        # Associate the conversation with the share
        logger.debug(f"Associating conversation {context.id} with share {share_id}")
        await ShareManager.set_conversation_role(context, share_id, ConversationRole.COORDINATOR)

        # No need to set conversation role in share storage, as we use metadata
        logger.debug(f"Conversation {context.id} is Coordinator for share {share_id}")

        # Note: Conversation linking is now handled via JSON data, no directory needed

        return share_id

    @staticmethod
    async def set_conversation_role(context: ConversationContext, share_id: str, role: ConversationRole) -> None:
        """
        Sets the role of a conversation in a knowledge transfer share.
        """
        role_data = ConversationShareInfo(share_id=share_id, role=role, conversation_id=str(context.id))
        role_path = ShareStorageManager.get_conversation_role_file_path(context)
        write_model(role_path, role_data)

    @staticmethod
    async def get_conversation_role(
        context: ConversationContext,
    ) -> ConversationRole | None:
        """
        Gets the role of a conversation in a knowledge transfer.
        """
        role_path = ShareStorageManager.get_conversation_role_file_path(context)
        role_data = read_model(role_path, ConversationShareInfo)

        if role_data:
            return role_data.role

        return ConversationRole.COORDINATOR

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
        share URL that can be used by team members to join the knowledge transfer.

        Args:
            context: Current conversation context
            share_id: ID of the share

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
        knowledge_package = await ShareManager.get_share(context)
        if knowledge_package:
            knowledge_package.shared_conversation_id = str(conversation.id)
            knowledge_package.share_url = share_url
            knowledge_package.updated_at = datetime.now(UTC)
            ShareStorage.write_share(share_id, knowledge_package)
        else:
            raise ValueError(f"KnowledgePackage info not found for share ID: {share_id}")

        return share_url

    @staticmethod
    async def get_shared_conversation_id(context: ConversationContext) -> str | None:
        """
        Retrieves the share ID and finds the associated shareable template conversation ID.
        """
        try:
            share = await ShareManager.get_share(context)
            if not share.shared_conversation_id:
                return None
            return share.shared_conversation_id
        except Exception as e:
            logger.error(f"Error getting shared conversation ID: {e}")
            return None

    @staticmethod
    async def join_share(
        context: ConversationContext,
        share_id: str,
        role: ConversationRole = ConversationRole.TEAM,
    ) -> None:
        """
        Joins an existing share.

        Args:
            context: Current conversation context
            share_id: ID of the share to join
            role: Role for this conversation (COORDINATOR or TEAM)
        """
        if not ShareStorageManager.share_exists(share_id):
            raise ValueError(f"Cannot join share: share {share_id} does not exist")

        # Associate the conversation with the share
        await ShareManager.set_conversation_role(context, share_id, role)

        # Role is set in metadata, not in storage

        logger.info(f"Joined share {share_id} as {role.value}")

    @staticmethod
    async def get_share_id(context: ConversationContext) -> str:
        try:
            share_path = ShareStorageManager.get_conversation_role_file_path(context)
            share_data = read_model(share_path, ConversationShareInfo)
            if share_data:
                return share_data.share_id
            else:
                raise NoShareException
        except Error as e:
            raise NoShareFoundError(str(e)) from e

    @staticmethod
    async def get_share(context: ConversationContext) -> KnowledgePackage:
        """Gets the share information for the current conversation's share."""
        try:
            share_id = await ShareManager.get_share_id(context)
            share = ShareStorage.read_share(share_id)
            if share:
                # Load the separate log file if not already loaded
                if not share.log:
                    share.log = ShareStorage.read_share_log(share_id)
                return share
            else:
                raise NoShareException
        except Error as e:
            raise NoShareFoundError(str(e)) from e

    @staticmethod
    async def set_share(context: ConversationContext, share: KnowledgePackage) -> None:
        """
        Sets the share information for the current conversation's share.

        This updates the share data in storage, including the log if it exists.
        """
        share_id = await ShareManager.get_share_id(context)
        ShareStorage.write_share(share_id, share)

        # If the log exists, write it as well
        if share.log:
            ShareStorage.write_share_log(share_id, share.log)

    @staticmethod
    async def get_linked_conversations(context: ConversationContext) -> list[str]:
        """
        Gets all conversations linked to this one through the same knowledge transfer share.
        """
        try:
            share = await ShareManager.get_share(context)
            conversations = []

            # Add coordinator conversation
            if share.coordinator_conversation_id:
                conversations.append(share.coordinator_conversation_id)

            # Add shared template conversation (though usually excluded from notifications)
            if share.shared_conversation_id and share.shared_conversation_id:
                conversations.append(share.shared_conversation_id)

            # Add all team conversations
            for conversation_id in share.team_conversations:
                conversations.append(conversation_id)

            return []

        except Exception as e:
            logger.error(f"Error getting linked conversations: {e}")
            return []

    @staticmethod
    async def _capture_redeemer_info(context: ConversationContext, share_id: str) -> None:
        """
        Captures the redeemer (first non-assistant participant) information and stores it in the knowledge package.
        Only captures info for actual team member conversations, not coordinator or shared conversations.
        """
        try:
            knowledge_package = ShareStorage.read_share(share_id)
            if not knowledge_package:
                logger.warning(f"Could not load knowledge package {share_id} to capture redeemer info")
                return

            conversation_id = str(context.id)

            # Skip if this is the coordinator conversation
            if conversation_id == knowledge_package.coordinator_conversation_id:
                logger.debug(f"Skipping redeemer capture for coordinator conversation {conversation_id}")
                return

            # Skip if this is the shared conversation template
            if conversation_id == knowledge_package.shared_conversation_id:
                logger.debug(f"Skipping redeemer capture for shared conversation template {conversation_id}")
                return

            # If we get here, it's a team member conversation - capture redeemer info
            # Get current user information (the redeemer)
            user_id, user_name = await get_current_user(context)

            if not user_id or not user_name:
                logger.warning(f"Could not identify redeemer for conversation {conversation_id}")
                return

            # Create team conversation info
            team_conversation_info = TeamConversationInfo(
                conversation_id=conversation_id,
                redeemer_user_id=user_id,
                redeemer_name=user_name,
            )

            # Add to knowledge package
            knowledge_package.team_conversations[conversation_id] = team_conversation_info

            # Save the updated knowledge package
            ShareStorage.write_share(share_id, knowledge_package)
            logger.debug(f"Captured redeemer info for team conversation {conversation_id}: {user_name} ({user_id})")

        except Exception as e:
            logger.error(f"Error capturing redeemer info: {e}")
            # Don't re-raise - this is not critical for the association process

    @staticmethod
    async def get_share_log(
        context: ConversationContext,
    ) -> KnowledgePackageLog | None:
        """Gets the knowledge transfer log for the current conversation's share."""
        try:
            share_id = await ShareManager.get_share_id(context)
            return ShareStorage.read_share_log(share_id)
        except Error as e:
            logger.error(f"Error reading share log: {e}")
            return None

    @staticmethod
    async def append_coordinator_message(
        context: ConversationContext,
        message_id: str,
        content: str,
        sender_name: str,
        is_assistant: bool = False,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Appends a message to the coordinator conversation log.

        This is used to log messages sent by the coordinator in the knowledge transfer process.
        """
        try:
            share_id = await ShareManager.get_share_id(context)
            ShareStorage.append_coordinator_message(
                share_id=share_id,
                message_id=message_id,
                content=content,
                sender_name=sender_name,
                is_assistant=is_assistant,
                timestamp=timestamp or datetime.now(UTC),
            )
        except Exception as e:
            logger.error(f"Error appending coordinator message: {e}")

    @staticmethod
    async def get_coordinator_conversation(
        context: ConversationContext,
    ) -> CoordinatorConversationMessages | None:
        """
        Gets the coordinator conversation.
        """
        share_id = await ShareManager.get_share_id(context)
        if share_id:
            return ShareStorage.read_coordinator_conversation(share_id)
        return None

    @staticmethod
    async def log_share_event(
        context: ConversationContext,
        entry_type: str,
        message: str,
        related_entity_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Logs an event to the knowledge transfer log.

        Args:
            context: Current conversation context
            entry_type: Type of log entry
            message: Log message
            related_entity_id: Optional ID of a related entity
            metadata: Optional additional metadata
        """
        try:
            share_id = await ShareManager.get_share_id(context)

            await ShareStorage.log_share_event(
                context=context,
                share_id=share_id,
                entry_type=entry_type,
                message=message,
                related_entity_id=related_entity_id,
                metadata=metadata,
            )
        except Error as e:
            logger.error(f"Error logging share event: {e}")
