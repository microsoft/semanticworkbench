"""
Coordinator support and helper functions for Knowledge Transfer Assistant.

Provides next action suggestions and other coordinator utilities.
"""

from typing import Optional

from semantic_workbench_assistant.assistant_app import ConversationContext

from ..data import RequestStatus
from ..domain.knowledge_transfer_manager import KnowledgeTransferManager
from ..logging import logger
from ..domain.share_manager import ShareManager


class CoordinatorSupport:
    """Provides support utilities for coordinators."""

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
            share_id = await ShareManager.get_share_id(context)
            if not share_id:
                logger.warning("No share ID found for this conversation")
                return None

            package = await ShareManager.get_share(context)
            if not package:
                return None

            brief = package.brief
            requests = package.requests
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
                return "Your package needs a short introduction that will orient your team. Let's write a knowledge brief next. The knowledge brief helps your team understand the purpose of this knowledge transfer and will be visible to all team members in their side panel."

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
                    return f"The learning objective '{name}' doesn't have any outcomes yet. Let's define what your team should accomplish to meet it."

            # 7. Ready for transfer but not yet shared
            if KnowledgeTransferManager.is_ready_for_transfer(
                package
            ) and not KnowledgeTransferManager.is_actively_sharing(package):
                return "Your knowledge package is ready to share. Would you like to create a message and generate the invitation link?"

            # 8. Actively sharing - monitor and support ongoing transfer
            if KnowledgeTransferManager.is_actively_sharing(package):
                if package.is_intended_to_accomplish_outcomes and not KnowledgeTransferManager._is_transfer_complete(
                    package
                ):
                    team_count = len(package.team_conversations)
                    return f"Great! Your knowledge is being shared with {team_count} team member{'s' if team_count != 1 else ''}. You can continue improving the package or respond to information requests as they come in."
                else:
                    return "Your knowledge transfer is in progress. You can continue improving the package or respond to information requests as they come in."

            # 9. Default: General support
            return "Your package is available. You can continue improving it or respond to new information requests as they come in."

        except Exception as e:
            logger.exception(f"Error generating next action suggestion: {e}")
            return None
