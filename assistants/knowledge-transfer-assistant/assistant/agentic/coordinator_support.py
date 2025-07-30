"""
Coordinator support and helper functions for Knowledge Transfer Assistant.

Provides next action suggestions and other coordinator utilities.
"""

from semantic_workbench_assistant.assistant_app import ConversationContext

from assistant.data import RequestStatus
from assistant.domain import ShareManager, TransferManager
from assistant.logging import logger


class CoordinatorSupport:
    """Provides support utilities for coordinators."""

    @staticmethod
    async def get_coordinator_next_action_suggestion(
        context: ConversationContext,
    ) -> str | None:
        """
        Generate next action suggestions for the coordinator based on the knowledge transfer state.

        This output is passed to the assistant and helps guide the conversation toward completing or improving
        the knowledge share in a helpful, structured way.

        Returns:
            A user-facing suggestion string, or None if no suggestion is needed.
        """
        try:
            share_id = await ShareManager.get_share_id(context)
            if not share_id:
                logger.warning("No share ID found for this conversation")
                return None

            share = await ShareManager.get_share(context)
            if not share:
                return None

            brief = share.brief
            requests = share.requests
            active_requests = [r for r in requests if r.status == RequestStatus.NEW]

            # 1. Unresolved requests come first
            if active_requests:
                request = active_requests[0]
                return (
                    f"There are {len(active_requests)} unanswered questions from team members. "
                    f'One of them is: "{request.title}" Let\'s work on answering it.'
                )

            # 2. Audience not yet defined
            if not share.audience:
                return (
                    "Let's start by defining who your audience is. "
                    "Who is this knowledge for, and what's their background?"
                )

            # 3. Knowledge not yet organized
            if not share.knowledge_organized:
                return (
                    "Next, let's organize your knowledge. Upload any relevant files or describe the knowledge "
                    "you want to transfer. When you're ready, I can mark the knowledge as organized."
                )

            # 4. Brief not yet written
            if not brief:
                return (
                    "Your knowledge share-out needs a short introduction that will orient your team. "
                    "Let's write a knowledge brief next. The knowledge brief helps your team understand "
                    "the purpose of this knowledge transfer and will be visible to all team members in their side panel."  # noqa: E501
                )

            # 5. If intended to have outcomes but none defined yet
            if share.is_intended_to_accomplish_outcomes and not share.learning_objectives:
                return (
                    "Would you like your team to achieve any specific outcomes? If so, let's define some learning objectives. "  # noqa: E501
                    "If not, you can mark this share-out as 'exploratory' instead."
                )

            # 6. Objectives exist, but missing outcomes
            if share.is_intended_to_accomplish_outcomes:
                incomplete_objectives = [obj for obj in share.learning_objectives if not obj.learning_outcomes]
                if incomplete_objectives:
                    name = incomplete_objectives[0].name
                    return (
                        f"The learning objective '{name}' doesn't have any outcomes yet. "
                        f"Let's define what your team should accomplish to meet it."
                    )

            # 7. Ready for transfer but not yet shared
            if TransferManager.is_ready_for_transfer(share) and not TransferManager.is_actively_sharing(share):
                return (
                    "Your knowledge is ready to share. "
                    "Would you like to create a message and generate the invitation link?"
                )

            # 8. Actively sharing - monitor and support ongoing transfer
            if TransferManager.is_actively_sharing(share):
                if share.is_intended_to_accomplish_outcomes and not TransferManager._is_transfer_complete(share):
                    team_count = len(share.team_conversations)
                    return (
                        f"Great! Your knowledge is being shared with {team_count} team member"
                        f"{'s' if team_count != 1 else ''}. You can continue improving the knowledge share or "
                        f"respond to information requests as they come in."
                    )
                else:
                    return (
                        "Your knowledge transfer is in progress. You can continue improving the knowledge share or "
                        "respond to information requests as they come in."
                    )

            # 9. Default: General support
            return (
                "Your knowledge share is available. You can continue improving it or "
                "respond to new information requests as they come in."
            )

        except Exception as e:
            logger.exception(f"Error generating next action suggestion: {e}")
            return None
