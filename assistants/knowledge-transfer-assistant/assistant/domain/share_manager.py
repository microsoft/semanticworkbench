"""
Share/Project management operations for Knowledge Transfer Assistant.

Handles creation, joining, and basic share operations.
"""

import uuid
from datetime import datetime
from typing import Optional

from semantic_workbench_api_model.workbench_model import (
    ConversationPermission,
    NewConversation,
    NewConversationShare,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..conversation_share_link import ConversationKnowledgePackageManager
from ..data import KnowledgePackage, KnowledgePackageLog
from ..logging import logger
from ..storage import ShareStorage, ShareStorageManager
from ..storage_models import ConversationRole
from ..utils import get_current_user


class ShareManager:
    """Manages knowledge share creation, joining, and basic operations."""

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
        knowledge_package = ShareStorage.read_share(share_id)
        if knowledge_package:
            knowledge_package.shared_conversation_id = str(conversation.id)
            knowledge_package.share_url = share_url
            knowledge_package.updated_at = datetime.utcnow()
            ShareStorage.write_share(share_id, knowledge_package)
        else:
            raise ValueError(f"KnowledgePackage info not found for share ID: {share_id}")

        return share_url

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
        await ConversationKnowledgePackageManager.associate_conversation_with_share(context, share_id)

        # No need to set conversation role in share storage, as we use metadata
        logger.debug(f"Conversation {context.id} is Coordinator for share {share_id}")

        # Note: Conversation linking is now handled via JSON data, no directory needed

        return share_id

    @staticmethod
    async def join_share(
        context: ConversationContext,
        share_id: str,
        role: ConversationRole = ConversationRole.TEAM,
    ) -> bool:
        """
        Joins an existing share.

        Args:
            context: Current conversation context
            share_id: ID of the share to join
            role: Role for this conversation (COORDINATOR or TEAM)

        Returns:
            True if joined successfully, False otherwise
        """
        try:
            if not ShareStorageManager.share_exists(share_id):
                logger.error(f"Cannot join share: share {share_id} does not exist")
                return False

            # Associate the conversation with the share
            await ConversationKnowledgePackageManager.associate_conversation_with_share(context, share_id)

            # Role is set in metadata, not in storage

            logger.info(f"Joined share {share_id} as {role.value}")
            return True

        except Exception as e:
            logger.exception(f"Error joining share: {e}")
            return False

    @staticmethod
    async def get_share_id(context: ConversationContext) -> Optional[str]:
        """
        Gets the share ID associated with the current conversation.

        Every conversation that's part of a knowledge transfer share has an
        associated share ID. This method retrieves that ID, which is used for
        accessing share-related data structures.

        Args:
            context: Current conversation context

        Returns:
            The share ID string if the conversation is part of a share, None
            otherwise
        """
        return await ConversationKnowledgePackageManager.get_associated_share_id(context)

    @staticmethod
    async def get_share_role(context: ConversationContext) -> Optional[ConversationRole]:
        """
        Gets the role of the current conversation in its share.

        Each conversation participating in a share has a specific role:
        - COORDINATOR: The primary conversation that created and manages the share
        - TEAM: Conversations where team members are carrying out the share tasks

        This method examines the conversation metadata to determine the role
        of the current conversation in the share. The role is stored in the
        conversation metadata as "project_role".

        Args:
            context: Current conversation context

        Returns:
            The role (KnowledgePackageRole.COORDINATOR or KnowledgePackageRole.TEAM) if the conversation
            is part of a share, None otherwise
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
            logger.exception(f"Error detecting share role: {e}")
            # Default to None if we can't determine
            return None

    @staticmethod
    async def get_share_log(context: ConversationContext) -> Optional[KnowledgePackageLog]:
        """Gets the knowledge transfer log for the current conversation's share."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return None

        return ShareStorage.read_share_log(share_id)

    @staticmethod
    async def get_share(context: ConversationContext) -> Optional[KnowledgePackage]:
        """Gets the share information for the current conversation's share."""
        share_id = await ShareManager.get_share_id(context)
        if not share_id:
            return None
        share = ShareStorage.read_share(share_id)
        if share:
            # Load the separate log file if not already loaded
            if not share.log:
                share.log = ShareStorage.read_share_log(share_id)
        else:
            # Create a new package if it doesn't exist, but this should be rare in get_share
            return None
        return share

    @staticmethod
    async def get_share_info(
        context: ConversationContext, share_id: Optional[str] = None
    ) -> Optional[KnowledgePackage]:
        """
        Gets the share information including share URL and team conversation details.

        Args:
            context: Current conversation context
            share_id: Optional share ID (if not provided, will be retrieved from context)

        Returns:
            KnowledgePackageInfo object or None if not found
        """
        try:
            if not share_id:
                share_id = await ShareManager.get_share_id(context)
                if not share_id:
                    return None

            share_info = ShareStorage.read_share_info(share_id)
            return share_info

        except Exception as e:
            logger.exception(f"Error getting share info: {e}")
            return None
