"""
Manager directory for Knowledge Transfer Assistant.

This module provides the main KnowledgeTransferManager class for project management.
"""

from .audience_manager import AudienceManager
from .information_request_manager import InformationRequestManager
from .knowledge_brief_manager import KnowledgeBriefManager
from .knowledge_digest_manager import KnowledgeDigestManager
from .learning_objectives_manager import LearningObjectivesManager
from .share_manager import ShareManager
from .transfer_manager import TransferManager

__all__ = [
    "TransferManager",
    "InformationRequestManager",
    "KnowledgeBriefManager",
    "KnowledgeDigestManager",
    "LearningObjectivesManager",
    "AudienceManager",
    "ShareManager",
]
