"""
Artifact messaging system for the Mission Assistant.

This module handles sending and receiving artifacts between linked conversations.
It provides the core functionality for the message-based artifact sharing approach.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Type, TypeVar, cast

from semantic_workbench_api_model.workbench_model import (
    ConversationMessage,
    MessageType,
    NewConversationMessage,
)
from semantic_workbench_assistant.assistant_app import ConversationContext

from .artifacts import (
    ArtifactMessage,
    ArtifactType,
    ArtifactVersion,
    BaseArtifact,
    FieldRequest,
    KBSection,
    LogEntry,
    LogEntryType,
    MissionBriefing,
    MissionGoal,
    MissionKB,
    MissionLog,
    MissionStatus,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
    get_artifact_type,
)
from .context_types import ConversationContextExt
from .mission import ConversationClientManager, MissionStateManager

T = TypeVar("T")

logger = logging.getLogger(__name__)

# Maximum size for message metadata (conservative limit)
MAX_METADATA_SIZE = 100000  # Characters


class ArtifactMessenger:
    """Handles sending and receiving artifacts between linked conversations."""

    @staticmethod
    def serialize_artifact(artifact: BaseArtifact) -> Dict[str, Any]:
        """
        Serializes an artifact model to a dictionary.

        Args:
            artifact: The artifact to serialize

        Returns:
            Dictionary representation of the artifact
        """
        return json.loads(artifact.model_dump_json())

    @staticmethod
    def deserialize_artifact(data: Dict[str, Any], artifact_class: Type[BaseArtifact]) -> BaseArtifact:
        """
        Deserializes a dictionary into an artifact model.

        Args:
            data: Dictionary containing artifact data
            artifact_class: The Pydantic model class to deserialize into

        Returns:
            Instantiated artifact model
        """
        return artifact_class.model_validate(data)

    @staticmethod
    def create_artifact_message(
        artifact: BaseArtifact,
        source_conversation_id: str,
        target_conversation_id: str,
        is_notification_only: bool = False,
    ) -> ArtifactMessage:
        """
        Creates a message containing artifact data for cross-conversation sharing.

        Args:
            artifact: The artifact to share
            source_conversation_id: ID of the conversation sending the artifact
            target_conversation_id: ID of the conversation receiving the artifact
            is_notification_only: If True, only notification metadata is included

        Returns:
            Artifact message ready for transmission
        """
        # Create version information
        version_info = ArtifactVersion(
            artifact_id=artifact.artifact_id,
            artifact_type=artifact.artifact_type,
            version=artifact.version,
            timestamp=artifact.updated_at,
            updated_by=artifact.updated_by,
        )

        # Serialize the artifact
        artifact_data = ArtifactMessenger.serialize_artifact(artifact)

        # If this is just a notification, remove large data fields
        if is_notification_only:
            # Keep only essential identification fields
            notification_data = {
                "artifact_id": artifact.artifact_id,
                "artifact_type": artifact.artifact_type,
                "version": artifact.version,
                "updated_at": artifact.updated_at.isoformat(),
                "updated_by": artifact.updated_by,
            }
            artifact_data = notification_data

        # Create the message
        return ArtifactMessage(
            artifact_type=artifact.artifact_type,
            artifact_data=artifact_data,
            version_info=version_info,
            source_conversation_id=source_conversation_id,
            target_conversation_id=target_conversation_id,
            is_notification_only=is_notification_only,
        )

    @staticmethod
    async def send_artifact(
        context: ConversationContext,
        artifact: BaseArtifact,
        target_conversation_id: str,
        notification_only: bool = False,
    ) -> bool:
        """
        Sends an artifact to another conversation via message metadata.

        Args:
            context: Current conversation context
            artifact: The artifact to send
            target_conversation_id: ID of the target conversation
            notification_only: If True, only sends notification without full data

        Returns:
            True if artifact was sent successfully, False otherwise
        """
        try:
            # Create the artifact message
            artifact_message = ArtifactMessenger.create_artifact_message(
                artifact=artifact,
                source_conversation_id=str(cast(ConversationContextExt, context).conversation.id),
                target_conversation_id=target_conversation_id,
                is_notification_only=notification_only,
            )

            # Serialize to JSON for metadata
            artifact_message_json = json.loads(artifact_message.model_dump_json())

            # Get client for target conversation
            target_client = ConversationClientManager.get_conversation_client(context, target_conversation_id)

            # Verify message size
            message_size = len(json.dumps(artifact_message_json))
            if message_size > MAX_METADATA_SIZE:
                logger.warning(f"Artifact message too large ({message_size} chars), enforcing notification only")
                # Fall back to notification-only mode for large artifacts
                return await ArtifactMessenger.send_artifact(
                    context, artifact, target_conversation_id, notification_only=True
                )

            # Create the metadata for the message
            metadata = {
                "artifact_message": artifact_message_json,
                "generated_content": False,
            }

            # Determine the appropriate message content based on artifact type
            type_name = artifact.artifact_type.value.replace("_", " ").title()
            if notification_only:
                message_content = f"[Notification: {type_name} updated (version {artifact.version})]"
            else:
                message_content = f"[{type_name} Synchronization (version {artifact.version})]"

            # Send the message with the artifact in metadata
            await target_client.send_messages(
                NewConversationMessage(
                    content=message_content,
                    message_type=MessageType.notice,  # Use notice type for system messages
                    metadata=metadata,
                )
            )

            logger.info(
                f"Sent artifact {artifact.artifact_id} ({artifact.artifact_type}) to conversation {target_conversation_id}"
            )
            return True

        except Exception as e:
            logger.exception(f"Error sending artifact: {e}")
            return False

    @staticmethod
    async def process_artifact_message(
        context: ConversationContext, message: ConversationMessage
    ) -> Optional[BaseArtifact]:
        """
        Processes a received artifact message and updates local storage.

        Args:
            context: Current conversation context
            message: The message containing the artifact

        Returns:
            The processed artifact if successful, None otherwise
        """
        try:
            # Extract the artifact message from metadata
            metadata = message.metadata or {}
            artifact_message_data = metadata.get("artifact_message")
            if not artifact_message_data:
                return None

            # Parse the artifact message
            artifact_message = ArtifactMessage.model_validate(artifact_message_data)

            # If this is just a notification, request the full artifact
            if artifact_message.is_notification_only:
                await ArtifactMessenger.request_full_artifact(context, artifact_message)
                return None

            # Determine the artifact type and deserialize
            artifact_data = artifact_message.artifact_data
            artifact_type = artifact_message.artifact_type

            # Convert to the appropriate artifact class
            artifact = None
            if artifact_type == ArtifactType.MISSION_BRIEFING:
                artifact = ArtifactMessenger.deserialize_artifact(artifact_data, MissionBriefing)
            elif artifact_type == ArtifactType.MISSION_KB:
                artifact = ArtifactMessenger.deserialize_artifact(artifact_data, MissionKB)
            elif artifact_type == ArtifactType.MISSION_STATUS:
                artifact = ArtifactMessenger.deserialize_artifact(artifact_data, MissionStatus)
            elif artifact_type == ArtifactType.FIELD_REQUEST:
                artifact = ArtifactMessenger.deserialize_artifact(artifact_data, FieldRequest)
            elif artifact_type == ArtifactType.MISSION_LOG:
                artifact = ArtifactMessenger.deserialize_artifact(artifact_data, MissionLog)

            if artifact:
                # Save the artifact to local storage
                await ArtifactMessenger.save_artifact(context, artifact)

                # Log the receipt of the artifact
                logger.info(f"Received and saved artifact {artifact.artifact_id} ({artifact.artifact_type})")

                # Add an entry to the mission log
                await ArtifactMessenger.log_artifact_update(
                    context,
                    artifact.artifact_id,
                    artifact.artifact_type,
                    artifact.updated_by,
                    artifact.version,
                )

                return artifact

            return None

        except Exception as e:
            logger.exception(f"Error processing artifact message: {e}")
            return None

    @staticmethod
    async def request_full_artifact(context: ConversationContext, notification: ArtifactMessage) -> bool:
        """
        Requests the full artifact data after receiving a notification.

        Args:
            context: Current conversation context
            notification: The notification message

        Returns:
            True if request was sent successfully, False otherwise
        """
        try:
            # Get the source conversation client
            source_client = ConversationClientManager.get_conversation_client(
                context, notification.source_conversation_id
            )

            # Create request metadata
            request_metadata = {
                "artifact_request": {
                    "artifact_id": notification.version_info.artifact_id,
                    "artifact_type": notification.version_info.artifact_type,
                    "requested_version": notification.version_info.version,
                    "requesting_conversation_id": str(context.id),
                }
            }

            # Send request message
            await source_client.send_messages(
                NewConversationMessage(
                    content=f"[Artifact Request: {notification.version_info.artifact_type.value.replace('_', ' ').title()} version {notification.version_info.version}]",
                    message_type=MessageType.notice,
                    metadata=request_metadata,
                )
            )

            logger.info(
                f"Requested full artifact {notification.version_info.artifact_id} from conversation {notification.source_conversation_id}"
            )
            return True

        except Exception as e:
            logger.exception(f"Error requesting full artifact: {e}")
            return False

    @staticmethod
    async def process_artifact_request(context: ConversationContext, message: ConversationMessage) -> bool:
        """
        Processes a request for a full artifact and sends it if available.

        Args:
            context: Current conversation context
            message: The message containing the artifact request

        Returns:
            True if artifact was sent successfully, False otherwise
        """
        try:
            # Extract the artifact request from metadata
            metadata = message.metadata or {}
            request_data = metadata.get("artifact_request")
            if not request_data:
                return False

            # Get artifact details
            artifact_id = request_data.get("artifact_id")
            artifact_type_str = request_data.get("artifact_type")
            requesting_conversation_id = request_data.get("requesting_conversation_id")

            if not all([artifact_id, artifact_type_str, requesting_conversation_id]):
                logger.warning("Incomplete artifact request, missing required fields")
                return False

            # Convert string to enum
            artifact_type = get_artifact_type(ArtifactType(artifact_type_str))

            # Load the requested artifact
            artifact = await ArtifactMessenger.load_artifact(context, artifact_id, artifact_type)
            if not artifact:
                logger.warning(f"Requested artifact {artifact_id} not found")
                return False

            # Send the full artifact
            return await ArtifactMessenger.send_artifact(
                context, artifact, requesting_conversation_id, notification_only=False
            )

        except Exception as e:
            logger.exception(f"Error processing artifact request: {e}")
            return False

    @staticmethod
    async def save_artifact(context: ConversationContext, artifact: BaseArtifact) -> bool:
        """
        Saves an artifact to local storage.

        Args:
            context: Current conversation context
            artifact: The artifact to save

        Returns:
            True if artifact was saved successfully, False otherwise
        """
        try:
            # Get the state manager's storage path
            storage_path = MissionStateManager.get_state_file_path(context).parent

            # Ensure artifacts directory exists
            artifacts_dir = storage_path / "artifacts"
            artifacts_dir.mkdir(exist_ok=True)

            # Create type-specific directory
            type_dir = artifacts_dir / artifact.artifact_type.value
            type_dir.mkdir(exist_ok=True)

            # Create file path for this artifact
            file_path = type_dir / f"{artifact.artifact_id}.json"

            # Check for existing artifact to handle versioning
            if file_path.exists():
                try:
                    existing_data = json.loads(file_path.read_text())
                    existing_version = existing_data.get("version", 0)

                    # Skip if this version is older than what we already have
                    if existing_version > artifact.version:
                        logger.info(f"Skipping save of older artifact version {artifact.version} < {existing_version}")
                        return False
                except Exception as e:
                    logger.warning(f"Error reading existing artifact: {e}, will overwrite")

            # Serialize the artifact
            artifact_json = artifact.model_dump_json(indent=2)

            # Write to file
            file_path.write_text(artifact_json)

            logger.info(f"Saved artifact {artifact.artifact_id} to {file_path}")
            return True

        except Exception as e:
            logger.exception(f"Error saving artifact: {e}")
            return False

    T = TypeVar("T")

    @staticmethod
    async def load_artifact(context: ConversationContext, artifact_id: str, artifact_type: Type[T]) -> Optional[T]:
        """
        Loads an artifact from local storage.

        Args:
            context: Current conversation context
            artifact_id: ID of the artifact to load
            artifact_type: Type of the artifact

        Returns:
            The loaded artifact (properly typed as its specific subclass) if found, None otherwise
        """
        try:
            # Get the state manager's storage path
            storage_path = MissionStateManager.get_state_file_path(context).parent

            # Construct the file path
            file_path = storage_path / "artifacts" / str(artifact_type) / f"{artifact_id}.json"

            if not file_path.exists():
                logger.warning(f"Artifact file not found: {file_path}")
                return None

            # Read the file
            artifact_json = file_path.read_text()
            artifact_data = json.loads(artifact_json)

            # Determine the appropriate class and deserialize
            artifact_class = None
            if artifact_type == ArtifactType.MISSION_BRIEFING:
                artifact_class = MissionBriefing
            elif artifact_type == ArtifactType.MISSION_KB:
                artifact_class = MissionKB
            elif artifact_type == ArtifactType.MISSION_STATUS:
                artifact_class = MissionStatus
            elif artifact_type == ArtifactType.FIELD_REQUEST:
                artifact_class = FieldRequest
            elif artifact_type == ArtifactType.MISSION_LOG:
                artifact_class = MissionLog

            if not artifact_class:
                logger.error(f"Unknown artifact type: {artifact_type}")
                return None

            # Deserialize
            return cast(T, artifact_class.model_validate(artifact_data))

        except Exception as e:
            logger.exception(f"Error loading artifact: {e}")
            return None

    @staticmethod
    async def get_artifacts_by_type(context: ConversationContext, artifact_type: Type[T]) -> List[T]:
        """
        Gets all artifacts of a specific type from local storage.

        Args:
            context: Current conversation context
            artifact_type: Type of artifacts to retrieve

        Returns:
            List of artifacts of the specified type (properly typed as their specific subclasses)
        """
        try:
            # Get the state manager's storage path
            storage_path = MissionStateManager.get_state_file_path(context).parent

            # Construct the directory path
            dir_path = storage_path / "artifacts" / str(artifact_type)

            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                return []

            # Determine the appropriate class
            artifact_class = None
            if artifact_type == ArtifactType.MISSION_BRIEFING:
                artifact_class = MissionBriefing
            elif artifact_type == ArtifactType.MISSION_KB:
                artifact_class = MissionKB
            elif artifact_type == ArtifactType.MISSION_STATUS:
                artifact_class = MissionStatus
            elif artifact_type == ArtifactType.FIELD_REQUEST:
                artifact_class = FieldRequest
            elif artifact_type == ArtifactType.MISSION_LOG:
                artifact_class = MissionLog

            if not artifact_class:
                logger.error(f"Unknown artifact type: {artifact_type}")
                return []

            # Get all JSON files in the directory
            artifacts = []
            for file_path in dir_path.glob("*.json"):
                try:
                    artifact_json = file_path.read_text()
                    artifact_data = json.loads(artifact_json)
                    artifact = artifact_class.model_validate(artifact_data)
                    artifacts.append(artifact)
                except Exception as e:
                    logger.warning(f"Error loading artifact from {file_path}: {e}")

            # Sort by updated_at, newest first
            artifacts.sort(key=lambda a: a.updated_at, reverse=True)
            return artifacts

        except Exception as e:
            logger.exception(f"Error getting artifacts by type: {e}")
            return []

    @staticmethod
    async def log_artifact_update(
        context: ConversationContext,
        artifact_id: str,
        artifact_type: ArtifactType,
        user_id: str,
        version: int,
        entry_type: Optional[LogEntryType] = None,
        custom_message: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Adds an entry to the mission log for an artifact update.

        Args:
            context: Current conversation context
            artifact_id: ID of the updated artifact
            artifact_type: Type of the artifact
            user_id: ID of the user who updated the artifact
            version: Version number of the update
            entry_type: Optional specific log entry type
            custom_message: Optional custom message for the log entry
            custom_metadata: Optional additional metadata for the log entry
        """
        try:
            # Get user information
            participants = await context.get_participants()
            user_name = "Unknown User"
            for participant in participants.participants:
                if participant.id == user_id:
                    user_name = participant.name
                    break

            # Generate appropriate message based on artifact type
            if custom_message:
                message = custom_message
            else:
                type_name = artifact_type.value.replace("_", " ").title()
                message = f"{type_name} updated to version {version}"

            # Set entry type
            from .artifacts import LogEntryType

            if entry_type is None:
                entry_type = LogEntryType.ARTIFACT_UPDATED

            # Set metadata
            metadata = {"version": version}
            if custom_metadata:
                metadata.update(custom_metadata)

            # Create log entry
            entry = LogEntry(
                entry_type=entry_type,
                message=message,
                user_id=user_id,
                user_name=user_name,
                artifact_id=artifact_id,
                artifact_type=artifact_type,
                metadata=metadata,
            )

            # Get existing mission log or create new one
            mission_logs = await ArtifactMessenger.get_artifacts_by_type(context, MissionLog)

            mission_log = None
            if mission_logs:
                mission_log = mission_logs[0]  # Use the most recent log
            else:
                # Create a new mission log
                log_entries: List[LogEntry] = []  # Create explicit empty list for clarity
                mission_log = MissionLog(
                    artifact_type=ArtifactType.MISSION_LOG,
                    created_by=user_id,
                    updated_by=user_id,
                    conversation_id=str(context.id),
                    entries=log_entries,  # Use explicitly created empty list
                )

            # Add entry to the log
            mission_log.entries.append(entry)
            mission_log.updated_at = datetime.utcnow()
            mission_log.updated_by = user_id
            mission_log.version += 1

            # Save the updated log
            await ArtifactMessenger.save_artifact(context, mission_log)

            # Synchronize log with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, mission_log, conv_id)

        except Exception as e:
            logger.exception(f"Error adding log entry: {e}")


class ArtifactManager:
    """
    High-level manager for creating, updating, and sharing artifacts
    between linked conversations.
    """

    @staticmethod
    async def create_mission_briefing(
        context: ConversationContext,
        mission_name: str,
        mission_description: str,
        goals: Optional[List[Dict]] = None,
    ) -> Tuple[bool, Optional[MissionBriefing]]:
        """
        Creates a new mission briefing and shares it with linked conversations.

        Args:
            context: Current conversation context
            mission_name: The name of the mission
            mission_description: Description of the mission
            goals: Optional list of goals with success criteria

        Returns:
            Tuple of (success, mission_briefing or None)
        """
        try:
            # Get current user information
            participants = await context.get_participants()
            current_user_id = None
            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, None

            # Create mission goals objects
            mission_goals = []
            if goals:
                for i, goal_data in enumerate(goals):
                    goal = MissionGoal(
                        name=goal_data.get("name", f"Goal {i + 1}"),
                        description=goal_data.get("description", ""),
                        priority=goal_data.get("priority", i + 1),
                        success_criteria=[],
                    )

                    # Add success criteria
                    criteria = goal_data.get("success_criteria", [])
                    for criterion in criteria:
                        goal.success_criteria.append(SuccessCriterion(description=criterion))

                    mission_goals.append(goal)

            # Create the mission briefing
            mission_briefing = MissionBriefing(
                mission_name=mission_name,
                mission_description=mission_description,
                goals=mission_goals,
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            # Save locally
            success = await ArtifactMessenger.save_artifact(context, mission_briefing)
            if not success:
                return False, None

            # Log the creation
            await ArtifactMessenger.log_artifact_update(
                context,
                mission_briefing.artifact_id,
                ArtifactType.MISSION_BRIEFING,
                current_user_id,
                mission_briefing.version,
            )

            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, mission_briefing, conv_id)

            return True, mission_briefing

        except Exception as e:
            logger.exception(f"Error creating mission briefing: {e}")
            return False, None

    @staticmethod
    async def update_mission_briefing(
        context: ConversationContext,
        briefing_id: str,
        updates: Dict[str, Any],
    ) -> Tuple[bool, Optional[MissionBriefing]]:
        """
        Updates an existing mission briefing and shares the updates.

        Args:
            context: Current conversation context
            briefing_id: ID of the briefing to update
            updates: Dictionary of fields to update

        Returns:
            Tuple of (success, updated_briefing)
        """
        try:
            # Get current user information
            participants = await context.get_participants()
            current_user_id = None
            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, None

            # Load the existing briefing
            briefing = await ArtifactMessenger.load_artifact(context, briefing_id, MissionBriefing)

            if not briefing:
                logger.warning(f"Mission briefing {briefing_id} not found")
                return False, None

            # Apply updates
            updated = False
            for field, value in updates.items():
                if hasattr(briefing, field) and field not in ["artifact_id", "artifact_type", "version"]:
                    setattr(briefing, field, value)
                    updated = True

            if not updated:
                logger.info("No updates applied to mission briefing")
                return True, briefing

            # Update metadata
            briefing.updated_at = datetime.utcnow()
            briefing.updated_by = current_user_id
            briefing.version += 1

            # Save locally
            success = await ArtifactMessenger.save_artifact(context, briefing)
            if not success:
                return False, None

            # Log the update
            await ArtifactMessenger.log_artifact_update(
                context,
                briefing.artifact_id,
                ArtifactType.MISSION_BRIEFING,
                current_user_id,
                briefing.version,
            )

            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, briefing, conv_id)

            return True, briefing

        except Exception as e:
            logger.exception(f"Error updating mission briefing: {e}")
            return False, None

    @staticmethod
    async def create_kb_section(
        context: ConversationContext,
        kb_id: Optional[str],
        title: str,
        content: str,
        order: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[MissionKB]]:
        """
        Creates a new section in the mission knowledge base.

        Args:
            context: Current conversation context
            kb_id: Optional ID of the knowledge base to update; if None, a new KB will be created
            title: Title of the new section
            content: Content for the section
            order: Display order of the section
            tags: Optional tags for categorization

        Returns:
            Tuple of (success, updated_kb)
        """
        try:
            # Get current user information
            participants = await context.get_participants()
            current_user_id = None
            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, None

            # Load existing KB or create new one
            kb = None
            if kb_id:
                kb = await ArtifactMessenger.load_artifact(context, kb_id, MissionKB)

            if not kb:
                # Create new KB if not found
                kb = MissionKB(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    sections={},
                )

            # Create new section
            section = KBSection(
                title=title,
                content=content,
                order=order,
                tags=tags or [],
                updated_by=current_user_id,
            )

            # Add to KB
            kb.sections[section.id] = section

            # Update metadata
            kb.updated_at = datetime.utcnow()
            kb.updated_by = current_user_id
            kb.version += 1

            # Save locally
            success = await ArtifactMessenger.save_artifact(context, kb)
            if not success:
                return False, None

            # Log the update
            await ArtifactMessenger.log_artifact_update(
                context,
                kb.artifact_id,
                ArtifactType.MISSION_KB,
                current_user_id,
                kb.version,
            )

            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, kb, conv_id)

            return True, kb

        except Exception as e:
            logger.exception(f"Error creating KB section: {e}")
            return False, None

    @staticmethod
    async def create_field_request(
        context: ConversationContext,
        title: str,
        description: str,
        priority: RequestPriority = RequestPriority.MEDIUM,
        related_goal_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[FieldRequest]]:
        """
        Creates a new field request (information need or blocker).

        Args:
            context: Current conversation context
            title: Title of the request
            description: Detailed description
            priority: Priority level
            related_goal_ids: Optional list of related goal IDs

        Returns:
            Tuple of (success, field_request)
        """
        try:
            # Get current user information
            participants = await context.get_participants()
            current_user_id = None
            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, None

            # Create the field request
            field_request = FieldRequest(
                title=title,
                description=description,
                priority=priority,
                related_goal_ids=related_goal_ids if related_goal_ids is not None else [],
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            # Save locally
            success = await ArtifactMessenger.save_artifact(context, field_request)
            if not success:
                return False, None

            # Log the creation
            await ArtifactMessenger.log_artifact_update(
                context,
                field_request.artifact_id,
                ArtifactType.FIELD_REQUEST,
                current_user_id,
                field_request.version,
            )

            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, field_request, conv_id)

            return True, field_request

        except Exception as e:
            logger.exception(f"Error creating field request: {e}")
            return False, None

    @staticmethod
    async def resolve_field_request(
        context: ConversationContext, request_id: str, resolution: str
    ) -> Tuple[bool, Optional[FieldRequest]]:
        """
        Resolves a field request by updating its status and adding resolution info.

        Args:
            context: Current conversation context
            request_id: ID of the field request to resolve
            resolution: Resolution information to add to the request

        Returns:
            Tuple of (success, field_request)
        """
        try:
            # Get current user information
            participants = await context.get_participants()
            current_user_id = None
            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, None

            # Load the field request
            field_request = await ArtifactMessenger.load_artifact(context, request_id, FieldRequest)

            if not field_request:
                # Try to find the request by ID from all field requests
                all_requests = await ArtifactMessenger.get_artifacts_by_type(context, FieldRequest)
                for request in all_requests:
                    if request.artifact_id == request_id:
                        field_request = request
                        break

                if not field_request:
                    logger.warning(f"Field request {request_id} not found")
                    return False, None

            # Only update if the request isn't already resolved
            if field_request.status == RequestStatus.RESOLVED:
                logger.info(f"Field request {request_id} is already resolved")
                return True, field_request

            # Update the field request
            field_request.status = RequestStatus.RESOLVED
            field_request.resolution = resolution
            field_request.resolved_at = datetime.utcnow()
            field_request.resolved_by = current_user_id

            # Add an update to the history
            field_request.updates.append({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user_id,
                "message": f"Request resolved: {resolution}",
                "status": RequestStatus.RESOLVED,
            })

            # Update metadata
            field_request.updated_at = datetime.utcnow()
            field_request.updated_by = current_user_id
            field_request.version += 1

            # Save locally
            success = await ArtifactMessenger.save_artifact(context, field_request)
            if not success:
                return False, None

            # Log the resolution
            await ArtifactMessenger.log_artifact_update(
                context,
                field_request.artifact_id,
                ArtifactType.FIELD_REQUEST,
                current_user_id,
                field_request.version,
            )

            # Also add a specific log entry for the resolution
            user_name = "Unknown User"
            for participant in participants.participants:
                if participant.id == current_user_id:
                    user_name = participant.name
                    break

            log_entry = LogEntry(
                entry_type=LogEntryType.REQUEST_RESOLVED,
                message=f"Field request '{field_request.title}' resolved",
                user_id=current_user_id,
                user_name=user_name,
                artifact_id=field_request.artifact_id,
                artifact_type=ArtifactType.FIELD_REQUEST,
                metadata={
                    "resolution": resolution,
                    "request_title": field_request.title,
                    "request_priority": field_request.priority,
                },
            )

            # Get existing mission log or create new one
            mission_logs = await ArtifactMessenger.get_artifacts_by_type(context, MissionLog)

            mission_log = None
            if mission_logs:
                mission_log = mission_logs[0]  # Use the most recent log
            else:
                # Create a new mission log
                mission_log = MissionLog(
                    artifact_type=ArtifactType.MISSION_LOG,
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    entries=[],
                )

            # Add entry to the log
            mission_log.entries.append(log_entry)
            mission_log.updated_at = datetime.utcnow()
            mission_log.updated_by = current_user_id
            mission_log.version += 1

            # Save the updated log
            await ArtifactMessenger.save_artifact(context, mission_log)

            # Update mission status if this was a blocker
            statuses = await ArtifactMessenger.get_artifacts_by_type(context, MissionStatus)
            status: MissionStatus | None = None
            if statuses:
                status = statuses[0]
                if field_request.artifact_id in status.active_blockers:
                    status.active_blockers.remove(field_request.artifact_id)
                    status.updated_at = datetime.utcnow()
                    status.updated_by = current_user_id
                    status.version += 1
                    await ArtifactMessenger.save_artifact(context, status)

            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    # Share both the resolved request and updated log
                    await ArtifactMessenger.send_artifact(context, field_request, conv_id)
                    await ArtifactMessenger.send_artifact(context, mission_log, conv_id)

                    # If we updated the status, share that too
                    if status and field_request.artifact_id in status.active_blockers:
                        await ArtifactMessenger.send_artifact(context, status, conv_id)

                    # Also send a direct notification to the requestor's conversation
                    if conv_id == field_request.conversation_id:
                        # Create a client for the requestor's conversation
                        target_client = ConversationClientManager.get_conversation_client(context, conv_id)

                        # Send a notification about the resolved request
                        await target_client.send_messages(
                            NewConversationMessage(
                                content=f"HQ has resolved your request '{field_request.title}': {resolution}",
                                message_type=MessageType.notice,
                            )
                        )

            return True, field_request

        except Exception as e:
            logger.exception(f"Error resolving field request: {e}")
            return False, None

    @staticmethod
    async def update_mission_status(
        context: ConversationContext,
        status_id: Optional[str] = None,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        status_message: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[MissionStatus]]:
        """
        Updates the mission status artifact.

        Args:
            context: Current conversation context
            status_id: ID of existing status to update (or None for new/latest)
            status: Overall mission status
            progress: Progress percentage (0-100)
            status_message: Custom status message
            next_actions: List of upcoming actions

        Returns:
            Tuple of (success, mission_status)
        """
        try:
            # Get current user information
            participants = await context.get_participants()
            current_user_id = None
            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                return False, None

            # Load existing status or create new one
            mission_status = None
            if status_id:
                mission_status = await ArtifactMessenger.load_artifact(context, status_id, MissionStatus)
            else:
                # Try to find the latest status
                statuses = await ArtifactMessenger.get_artifacts_by_type(context, MissionStatus)
                if statuses:
                    mission_status = statuses[0]  # Most recent first

            if not mission_status:
                # Create new status if not found
                mission_status = MissionStatus(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                )

                # Populate with data from mission briefing if available
                briefings = await ArtifactMessenger.get_artifacts_by_type(context, MissionBriefing)
                if briefings:
                    briefing = briefings[0]
                    mission_status.goals = briefing.goals

                    # Calculate total criteria
                    total_criteria = 0
                    for goal in briefing.goals:
                        total_criteria += len(goal.success_criteria)

                    mission_status.total_criteria = total_criteria

            # Apply updates
            if status:
                mission_status.status = status
            if progress is not None:
                mission_status.progress = min(max(progress, 0), 100)  # Ensure 0-100
            if status_message:
                mission_status.status_message = status_message
            if next_actions:
                mission_status.next_actions = next_actions

            # Update metadata
            mission_status.updated_at = datetime.utcnow()
            mission_status.updated_by = current_user_id
            mission_status.version += 1

            # Save locally
            success = await ArtifactMessenger.save_artifact(context, mission_status)
            if not success:
                return False, None

            # Log the update
            await ArtifactMessenger.log_artifact_update(
                context,
                mission_status.artifact_id,
                ArtifactType.MISSION_STATUS,
                current_user_id,
                mission_status.version,
            )

            # Share with linked conversations
            links = await MissionStateManager.get_links(context)
            for conv_id in links.linked_conversations:
                if conv_id != str(context.id):
                    await ArtifactMessenger.send_artifact(context, mission_status, conv_id)

            return True, mission_status

        except Exception as e:
            logger.exception(f"Error updating mission status: {e}")
            return False, None
