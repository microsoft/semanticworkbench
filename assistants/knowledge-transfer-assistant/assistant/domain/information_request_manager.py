"""
Information request management for Knowledge Transfer Assistant.

Handles information request creation, resolution, and retrieval.
"""

from datetime import datetime
from typing import List, Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from ..data import InformationRequest, InspectorTab, LogEntryType, RequestPriority, RequestStatus
from ..logging import logger
from ..notifications import Notifications
from ..storage import ShareStorage
from ..utils import require_current_user
from .share_manager import ShareManager


class InformationRequestManager:
    """Manages information request operations."""

    @staticmethod
    async def get_information_requests(
        context: ConversationContext,
    ) -> List[InformationRequest]:
        """Gets all information requests for the current conversation's share."""

        share_id = await ShareManager.get_share_id(context)
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
        try:
            share_id = await ShareManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot create information request: no share associated with this conversation")
                return False, None

            current_user_id = await require_current_user(context, "create information request")
            if not current_user_id:
                return False, None

            information_request = InformationRequest(
                title=title,
                description=description,
                priority=priority,
                related_objective_ids=related_objective_ids or [],
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            ShareStorage.write_information_request(share_id, information_request)

            await ShareManager.log_share_event(
                context=context,
                entry_type=LogEntryType.REQUEST_CREATED.value,
                message=f"Created information request: {title}",
                related_entity_id=information_request.request_id,
                metadata={
                    "priority": priority.value,
                    "request_id": information_request.request_id,
                },
            )

            await Notifications.notify_self_and_other(context, share_id, f"Information request '{title}' was created")
            await Notifications.notify_all_state_update(context, share_id, [InspectorTab.SHARING])

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
        try:
            share_id = await ShareManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot resolve information request: no share associated with this conversation")
                return False, None

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
            await ShareManager.log_share_event(
                context=context,
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

            await Notifications.notify_all_state_update(context, share_id, [InspectorTab.SHARING])
            await Notifications.notify_self_and_other(
                context,
                share_id,
                f"Information request '{information_request.title}' has been resolved: {resolution}",
                information_request.conversation_id if information_request.conversation_id != str(context.id) else None,
            )

            return True, information_request

        except Exception as e:
            logger.exception(f"Error resolving information request: {e}")
            return False, None

    @staticmethod
    async def delete_information_request(
        context: ConversationContext,
        request_id: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete an information request.

        Args:
            context: Current conversation context
            request_id: ID of the request to delete

        Returns:
            Tuple of (success, message)
        """
        try:
            share_id = await ShareManager.get_share_id(context)
            if not share_id:
                logger.error("Cannot delete information request: no share associated with this conversation")
                return False, "No knowledge package associated with this conversation."

            current_user_id = await require_current_user(context, "delete information request")
            if not current_user_id:
                return False, "Could not identify current user."

            # Get information request by ID
            cleaned_request_id = request_id.strip().replace('"', "").replace("'", "")
            information_request = ShareStorage.read_information_request(share_id, cleaned_request_id)
            if not information_request:
                return False, f"Information request with ID '{request_id}' not found."

            # Check ownership - only allow deletion by the creator
            if information_request.conversation_id != str(context.id):
                return False, "You can only delete information requests that you created."

            # Get user info for logging
            participants = await context.get_participants()
            current_username = "Team Member"
            for participant in participants.participants:
                if participant.role == "user":
                    current_username = participant.name
                    break

            request_title = information_request.title
            actual_request_id = information_request.request_id

            # Log the deletion
            await ShareManager.log_share_event(
                context=context,
                entry_type=LogEntryType.REQUEST_DELETED.value,
                message=f"Information request '{request_title}' was deleted by {current_username}",
                related_entity_id=actual_request_id,
                metadata={
                    "request_title": request_title,
                    "deleted_by": current_user_id,
                    "deleted_by_name": current_username,
                },
            )

            # Delete the information request from the main share data
            share = await ShareManager.get_share(context)
            if share and share.requests:
                share.requests = [req for req in share.requests if req.request_id != actual_request_id]
                await ShareManager.set_share(context, share)

            # Notify about the deletion
            await Notifications.notify_self_and_other(
                context,
                share_id,
                f"Information request '{request_title}' has been deleted.",
            )
            await Notifications.notify_all_state_update(context, share_id, [InspectorTab.SHARING])

            return True, f"Information request '{request_title}' has been successfully deleted."

        except Exception as e:
            logger.exception(f"Error deleting information request: {e}")
            return False, f"Error deleting information request: {str(e)}. Please try again later."
