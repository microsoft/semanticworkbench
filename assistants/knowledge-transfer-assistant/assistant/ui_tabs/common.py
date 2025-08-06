"""
Common utilities for inspector modules.
"""

from assistant.data import RequestPriority, RequestStatus, Share
from assistant.domain import TransferManager


def get_status_emoji(status: RequestStatus) -> str:
    """Get emoji representation for request status."""
    status_emojis = {
        RequestStatus.NEW: "🆕",  # New
        RequestStatus.ACKNOWLEDGED: "👀",  # Acknowledged/Seen
        RequestStatus.IN_PROGRESS: "⚡",  # In Progress
        RequestStatus.RESOLVED: "✅",  # Resolved/Complete
        RequestStatus.DEFERRED: "⏸️",  # Deferred/Paused
    }
    return status_emojis.get(status, "❓")  # Unknown status fallback


def get_priority_emoji(priority: RequestPriority) -> str:
    """Get emoji representation for request priority."""
    priority_emojis = {
        RequestPriority.LOW: "🔹",  # Low priority - blue diamond
        RequestPriority.MEDIUM: "🔶",  # Medium priority - orange diamond
        RequestPriority.HIGH: "🔴",  # High priority - red circle
        RequestPriority.CRITICAL: "⚠️",  # Critical priority - warning sign
    }
    return priority_emojis.get(priority, "🔹")  # Default to low priority emoji


def get_stage_label(share: Share, for_coordinator: bool = True) -> str:
    """
    Get a human-readable stage label based on current share state.

    Args:
        share: The knowledge share to get label for
        for_coordinator: Whether to return coordinator-focused or team-focused labels

    Returns:
        str: Stage label with emoji
    """
    if for_coordinator:
        # Coordinator perspective
        if not share.audience:
            return "🎯 Defining Audience"
        # elif not share.knowledge_organized:
        #     return "📋 Organizing Knowledge"
        elif not share.brief:
            return "📝 Creating Brief"
        elif share.is_intended_to_accomplish_outcomes and not share.learning_objectives:
            return "📚 Adding Objectives"
        elif not TransferManager.is_ready_for_transfer(share):
            return "📋 Finalizing Setup"
        elif share.is_intended_to_accomplish_outcomes and TransferManager._is_transfer_complete(share):
            return "✅ Transfer Complete"
        elif TransferManager.is_actively_sharing(share):
            return "📤 Sharing in Progress"
        else:
            return "🚀 Ready for Transfer"
    else:
        # Team perspective
        if not TransferManager.is_ready_for_transfer(share):
            return "⏳ Knowledge Being Organized"
        elif not share.is_intended_to_accomplish_outcomes:
            return "🔍 Exploring Knowledge"
        elif share.is_intended_to_accomplish_outcomes:
            return "🎯 Active Learning"
        else:
            return "🎯 Active Learning"
