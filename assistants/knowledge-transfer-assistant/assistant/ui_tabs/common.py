"""
Common utilities for inspector modules.
"""

from assistant.data import KnowledgePackage, RequestPriority, RequestStatus
from assistant.domain.knowledge_package_manager import KnowledgePackageManager


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


def get_stage_label(package: KnowledgePackage, for_coordinator: bool = True) -> str:
    """
    Get a human-readable stage label based on current package state.

    Args:
        package: The knowledge package to get label for
        for_coordinator: Whether to return coordinator-focused or team-focused labels

    Returns:
        str: Stage label with emoji
    """
    if package.archived:
        return "📦 Archived"

    if for_coordinator:
        # Coordinator perspective
        if not package.audience:
            return "🎯 Defining Audience"
        elif not package.knowledge_organized:
            return "📋 Organizing Knowledge"
        elif not package.brief:
            return "📝 Creating Brief"
        elif package.is_intended_to_accomplish_outcomes and not package.learning_objectives:
            return "📚 Adding Objectives"
        elif not KnowledgePackageManager.is_ready_for_transfer(package):
            return "📋 Finalizing Setup"
        elif package.is_intended_to_accomplish_outcomes and KnowledgePackageManager._is_transfer_complete(package):
            return "✅ Transfer Complete"
        elif KnowledgePackageManager.is_actively_sharing(package):
            return "📤 Sharing in Progress"
        else:
            return "🚀 Ready for Transfer"
    else:
        # Team perspective
        if package.archived:
            return "📦 Archived"
        elif not KnowledgePackageManager.is_ready_for_transfer(package):
            return "⏳ Knowledge Being Organized"
        elif not package.is_intended_to_accomplish_outcomes:
            return "🔍 Exploring Knowledge"
        elif package.is_intended_to_accomplish_outcomes:
            return "🎯 Active Learning"
        else:
            return "🎯 Active Learning"
