"""
Base classes and common imports for Knowledge Transfer Assistant manager modules.
"""

import re
import uuid
from datetime import datetime
from typing import List, Optional, Tuple

import openai_client
from semantic_workbench_api_model.workbench_model import (
    ConversationPermission,
    MessageType,
    NewConversation,
    NewConversationMessage,
    NewConversationShare,
    ParticipantRole,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from ..config import assistant_config
from ..conversation_clients import ConversationClientManager
from ..conversation_share_link import ConversationKnowledgePackageManager
from ..data import (
    InformationRequest,
    InspectorTab,
    KnowledgeBrief,
    KnowledgeDigest,
    KnowledgePackage,
    KnowledgePackageLog,
    LearningObjective,
    LearningOutcome,
    LogEntryType,
    RequestPriority,
    RequestStatus,
)
from ..logging import logger
from ..notifications import ProjectNotifier
from ..storage import ShareStorage, ShareStorageManager
from ..storage_models import ConversationRole
from ..utils import get_current_user, require_current_user


class ManagerBase:
    """Base class for manager functionality."""
    pass