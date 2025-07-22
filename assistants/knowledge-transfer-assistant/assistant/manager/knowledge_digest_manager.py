"""
Knowledge digest management for Knowledge Transfer Assistant.

Handles knowledge digest operations including auto-updating from conversations.
"""

from .base import (
    ManagerBase,
    re,
    datetime,
    Optional,
    Tuple,
    ConversationContext,
    ParticipantRole,
    KnowledgeDigest,
    InspectorTab,
    LogEntryType,
    ShareStorage,
    ProjectNotifier,
    assistant_config,
    openai_client,
    require_current_user,
    logger,
)


class KnowledgeDigestManager(ManagerBase):
    """Manages knowledge digest operations."""

    @staticmethod
    async def get_knowledge_digest(
        context: ConversationContext,
    ) -> Optional[KnowledgeDigest]:
        """Gets the knowledge digest for the current conversation's knowledge share."""
        from .share_management import ShareManagement
        
        share_id = await ShareManagement.get_share_id(context)
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
            from .share_management import ShareManagement
            
            # Get project ID
            share_id = await ShareManagement.get_share_id(context)
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
                await ShareStorage.refresh_all_share_uis(context, share_id, [InspectorTab.BRIEF])

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
            from .share_management import ShareManagement
            
            messages = await context.get_messages()
            chat_history = messages.messages

            # Get project ID
            share_id = await ShareManagement.get_share_id(context)
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
                    max_tokens=config.coordinator_config.max_digest_tokens,
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
            result = await KnowledgeDigestManager.update_knowledge_digest(
                context=context,
                content=digest_content,
                is_auto_generated=True,
                send_notification=False,
            )
            
            # Ensure debug panel refreshes after auto-update completes
            await ShareStorage.refresh_all_share_uis(context, share_id, [InspectorTab.DEBUG])
            
            return result

        except Exception as e:
            logger.exception(f"Error auto-updating knowledge digest: {e}")
            # Ensure debug panel refreshes even on error, but only if we have a share_id
            try:
                from .share_management import ShareManagement
                share_id = await ShareManagement.get_share_id(context)
                if share_id:
                    await ShareStorage.refresh_all_share_uis(context, share_id, [InspectorTab.DEBUG])
            except Exception as refresh_error:
                logger.warning(f"Failed to refresh UI after auto-update error: {refresh_error}")
            return False, None