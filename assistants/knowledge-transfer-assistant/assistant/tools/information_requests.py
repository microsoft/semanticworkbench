"""
Information request tools for Knowledge Transfer Assistant.

Tools for creating, managing, and resolving information requests between coordinators and team members.
"""

from typing import Literal

from assistant.data import ConversationRole, RequestPriority
from assistant.domain import InformationRequestManager, ShareManager
from assistant.logging import logger

from .base import ToolsBase


class InformationRequestTools(ToolsBase):
    """Tools for managing information requests."""

    async def create_information_request(
        self,
        title: str,
        description: str,
        priority: Literal["low", "medium", "high", "critical"],
    ) -> str:
        """
        Create an information request to send to the Coordinator for information that is unavailable to you or to report a blocker.

        WHEN TO USE:
        - When you need specific information or clarification from the Coordinator
        - When encountering a blocker that prevents progress on a learning objective
        - When requesting additional resources or documentation
        - When you need a decision from the Coordinator
        - When a user expressly asks for information or help with something unclear

        Set an appropriate priority based on how critical the information is:
        - "low": Nice to have, not blocking progress
        - "medium": Important but not immediate
        - "high": Important and somewhat urgent
        - "critical": Completely blocked, cannot proceed without this information

        Args:
            title: A concise, clear title that summarizes what information is needed
            description: A detailed explanation of what information is needed and why it's important
            priority: The priority level - must be one of: low, medium, high, critical

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.TEAM:
            return "Only Team members can create information requests."

        share = await ShareManager.get_share(self.context)
        if not share:
            return "No knowledge package associated with this conversation. Unable to create information request."

        priority_map = {
            "low": RequestPriority.LOW,
            "medium": RequestPriority.MEDIUM,
            "high": RequestPriority.HIGH,
            "critical": RequestPriority.CRITICAL,
        }
        priority_enum = priority_map.get(priority.lower(), RequestPriority.MEDIUM)

        success, request = await InformationRequestManager.create_information_request(
            context=self.context,
            title=title,
            description=description,
            priority=priority_enum,
        )
        if success and request:
            return f"Information request '{title}' created successfully. The Coordinator has been notified."
        else:
            return "Failed to create information request. Please try again."

    async def resolve_information_request(self, request_id: str, resolution: str) -> str:
        """
        Resolve an information request when you have the needed information to address it. Only use for active information requests. If there are no active information requests, this should never be called.

        WHEN TO USE:
        - When you have information that directly answers a team member's request
        - When the user has supplied information that resolves a pending request
        - When you've gathered enough details to unblock a team member
        - When a request is no longer relevant and should be closed with explanation

        Args:
            request_id: IMPORTANT! Use the exact Request ID (looks like "012345-abcd-67890"), NOT the title of the request
            resolution: Complete information that addresses the team member's question or blocker

        Returns:
            A message indicating success or failure
        """
        if self.role is not ConversationRole.COORDINATOR:
            # Add more detailed error message with guidance
            error_message = (
                "ERROR: Only Coordinator can resolve information requests. As a Team member, you should use "
                "create_information_request to send requests to the Coordinator, not try to resolve them yourself. "
                "The Coordinator must use resolve_information_request to respond to your requests."
            )
            logger.warning(f"Team member attempted to use resolve_information_request: {request_id}")
            return error_message

        share = await ShareManager.get_share(self.context)
        if not share:
            return "No knowledge package associated with this conversation. Unable to resolve information request."

        (
            success,
            information_request,
        ) = await InformationRequestManager.resolve_information_request(
            context=self.context, request_id=request_id, resolution=resolution
        )
        if success and information_request:
            return f"Information request '{information_request.title}' has been resolved."
        else:
            logger.warning(f"Failed to resolve information request. Invalid ID provided: '{request_id}'")
            return f'ERROR: Could not resolve information request with ID "{request_id}".'

    async def delete_information_request(self, request_id: str) -> str:
        """
        Delete an information request that is no longer needed.
        This completely removes the request from the system.

        Args:
            request_id: ID of the request to delete

        Returns:
            Message indicating success or failure
        """
        if self.role is not ConversationRole.TEAM:
            return "This tool is only available to Team members."

        success, message = await InformationRequestManager.delete_information_request(
            context=self.context, request_id=request_id
        )
        return message if message else ("Request deleted successfully." if success else "Failed to delete request.")
