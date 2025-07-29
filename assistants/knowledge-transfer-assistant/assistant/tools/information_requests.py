"""
Information request tools for Knowledge Transfer Assistant.

Tools for creating, managing, and resolving information requests between coordinators and team members.
"""

from typing import Literal

from assistant.data import RequestPriority
from assistant.domain import InformationRequestManager
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

        priority_map = {
            "low": RequestPriority.LOW,
            "medium": RequestPriority.MEDIUM,
            "high": RequestPriority.HIGH,
            "critical": RequestPriority.CRITICAL,
        }
        priority_enum = priority_map.get(priority.lower(), RequestPriority.MEDIUM)

        try:
            await InformationRequestManager.create_information_request(
                context=self.context,
                title=title,
                description=description,
                priority=priority_enum,
            )
            return f"Information request '{title}' created successfully. The Coordinator has been notified."
        except Exception as e:
            logger.exception(f"Failed to create information request: {e}")
            return f"Failed to create information request: {str(e)}"

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
        try:
            information_request = await InformationRequestManager.resolve_information_request(
                context=self.context, request_id=request_id, resolution=resolution
            )
            return f"Information request '{information_request.title}' has been resolved."
        except Exception as e:
            logger.exception(f"Failed to resolve information request: {e}")
            return f"ERROR: Could not resolve information request with ID '{request_id}': {str(e)}"

    async def delete_information_request(self, request_id: str) -> str:
        """
        Delete an information request that is no longer needed.
        This completely removes the request from the system.

        Args:
            request_id: ID of the request to delete

        Returns:
            Message indicating success or failure
        """
        try:
            message = await InformationRequestManager.delete_information_request(
                context=self.context, request_id=request_id
            )
            return message
        except Exception as e:
            logger.exception(f"Failed to delete information request: {e}")
            return f"Failed to delete information request: {str(e)}"
