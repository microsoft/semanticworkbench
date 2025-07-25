"""
Common utilities for inspector modules.
"""

from ..data import RequestPriority, RequestStatus

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