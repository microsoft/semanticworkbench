"""
Information request management for Knowledge Transfer Assistant.

Handles information request creation, resolution, and retrieval.
"""

from .base import (
    ManagerBase,
    datetime,
    Optional,
    List,
    Tuple,
    ConversationContext,
    InformationRequest,
    RequestPriority,
    RequestStatus,
    ShareStorage,
    LogEntryType,
    ProjectNotifier,
    ConversationClientManager,
    NewConversationMessage,
    MessageType,
    require_current_user,
    logger,
)


class InformationRequestManager(ManagerBase):
    """Manages information request operations."""

    @staticmethod
    async def get_information_requests(
        context: ConversationContext,
    ) -> List[InformationRequest]:
        """Gets all information requests for the current conversation's project."""
        from .share_management import ShareManagement
        
        share_id = await ShareManagement.get_share_id(context)
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
            from .share_management import ShareManagement
            
            # Get project ID
            share_id = await ShareManagement.get_share_id(context)
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
            from .share_management import ShareManagement
            
            # Get project ID
            share_id = await ShareManagement.get_share_id(context)
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