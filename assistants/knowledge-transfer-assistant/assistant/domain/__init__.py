"""
Manager directory for Knowledge Transfer Assistant.

This module provides the main KnowledgeTransferManager class for project management.
"""

from .information_request_manager import InformationRequestManager
from .knowledge_brief_manager import KnowledgeBriefManager
from .knowledge_digest_manager import KnowledgeDigestManager
from .learning_objectives_manager import LearningObjectivesManager
from .audience_manager import AudienceManager
from .share_manager import ShareManager
from .knowledge_transfer_manager import KnowledgeTransferManager

__all__ = [
    "KnowledgeTransferManager",
    "InformationRequestManager",
    "KnowledgeBriefManager",
    "KnowledgeDigestManager",
    "LearningObjectivesManager",
    "AudienceManager",
    "ShareManager",
]
