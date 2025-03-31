"""
Mission management logic for working with mission data.

This module provides the core business logic for working with mission data
without relying on the artifact abstraction.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from semantic_workbench_assistant.assistant_app import ConversationContext

from .mission_data import (
    FieldRequest,
    KBSection,
    LogEntry,
    LogEntryType,
    MissionBriefing,
    MissionGoal,
    MissionKB,
    MissionLog,
    MissionState,
    MissionStatus,
    RequestPriority,
    RequestStatus,
    SuccessCriterion,
)
from .mission_storage import (
    ConversationMissionManager,
    MissionNotifier,
    MissionRole,
    MissionStorage,
    MissionStorageManager,
)

logger = logging.getLogger(__name__)


class MissionManager:
    """
    Simplified mission manager that works directly with mission data
    instead of treating everything as generic artifacts.
    """

    @staticmethod
    async def create_mission(context: ConversationContext) -> Tuple[bool, str]:
        """
        Creates a new mission and associates the current conversation with it.

        Args:
            context: Current conversation context

        Returns:
            Tuple of (success, mission_id)
        """
        try:
            # Generate a unique mission ID
            mission_id = str(uuid.uuid4())

            # Associate the conversation with the mission
            await ConversationMissionManager.set_conversation_mission(context, mission_id)

            # Set this conversation as the HQ
            await ConversationMissionManager.set_conversation_role(context, mission_id, MissionRole.HQ)

            logger.info(f"Created new mission {mission_id} for conversation {context.id}")
            return True, mission_id

        except Exception as e:
            logger.exception(f"Error creating mission: {e}")
            return False, ""

    @staticmethod
    async def join_mission(
        context: ConversationContext, mission_id: str, role: MissionRole = MissionRole.FIELD
    ) -> bool:
        """
        Joins an existing mission.

        Args:
            context: Current conversation context
            mission_id: ID of the mission to join
            role: Role for this conversation (HQ or FIELD)

        Returns:
            True if joined successfully, False otherwise
        """
        try:
            # Check if mission exists
            if not MissionStorageManager.mission_exists(mission_id):
                logger.error(f"Cannot join mission: mission {mission_id} does not exist")
                return False

            # Associate the conversation with the mission
            await ConversationMissionManager.set_conversation_mission(context, mission_id)

            # Set the conversation role
            await ConversationMissionManager.set_conversation_role(context, mission_id, role)

            logger.info(f"Joined mission {mission_id} as {role.value}")
            return True

        except Exception as e:
            logger.exception(f"Error joining mission: {e}")
            return False

    @staticmethod
    async def get_mission_id(context: ConversationContext) -> Optional[str]:
        """Gets the mission ID associated with the current conversation."""
        return await ConversationMissionManager.get_conversation_mission(context)

    @staticmethod
    async def get_mission_role(context: ConversationContext) -> Optional[MissionRole]:
        """Gets the role of the current conversation in its mission."""
        return await ConversationMissionManager.get_conversation_role(context)

    @staticmethod
    async def get_mission_briefing(context: ConversationContext) -> Optional[MissionBriefing]:
        """Gets the mission briefing for the current conversation's mission."""
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            return None

        return MissionStorage.read_mission_briefing(mission_id)

    @staticmethod
    async def create_mission_briefing(
        context: ConversationContext,
        mission_name: str,
        mission_description: str,
        goals: Optional[List[Dict]] = None,
        timeline: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> Tuple[bool, Optional[MissionBriefing]]:
        """
        Creates a new mission briefing.

        Args:
            context: Current conversation context
            mission_name: Name of the mission
            mission_description: Description of the mission
            goals: Optional list of goals with success criteria
            timeline: Optional timeline for the mission
            additional_context: Optional additional context

        Returns:
            Tuple of (success, mission_briefing)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot create briefing: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot create briefing: no user found in conversation")
                return False, None

            # Create mission goals
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
            briefing = MissionBriefing(
                mission_name=mission_name,
                mission_description=mission_description,
                goals=mission_goals,
                timeline=timeline,
                additional_context=additional_context,
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            # Save the briefing
            MissionStorage.write_mission_briefing(mission_id, briefing)

            # Log the creation
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.BRIEFING_CREATED.value,
                message=f"Created mission briefing: {mission_name}",
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="briefing",
                message=f"Mission briefing updated: {mission_name}",
            )

            return True, briefing

        except Exception as e:
            logger.exception(f"Error creating mission briefing: {e}")
            return False, None

    @staticmethod
    async def update_mission_briefing(
        context: ConversationContext,
        updates: Dict[str, Any],
    ) -> bool:
        """
        Updates an existing mission briefing.

        Args:
            context: Current conversation context
            updates: Dictionary of fields to update

        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot update briefing: no mission associated with this conversation")
                return False

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot update briefing: no user found in conversation")
                return False

            # Load existing briefing
            briefing = MissionStorage.read_mission_briefing(mission_id)
            if not briefing:
                logger.error(f"Cannot update briefing: no briefing found for mission {mission_id}")
                return False

            # Apply updates, skipping protected fields
            updated = False
            protected_fields = ["created_by", "conversation_id", "created_at", "version"]

            for field, value in updates.items():
                if hasattr(briefing, field) and field not in protected_fields:
                    setattr(briefing, field, value)
                    updated = True

            if not updated:
                logger.info("No updates applied to briefing")
                return True

            # Update metadata
            briefing.updated_at = datetime.utcnow()
            briefing.updated_by = current_user_id
            briefing.version += 1

            # Save the updated briefing
            MissionStorage.write_mission_briefing(mission_id, briefing)

            # Log the update
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.BRIEFING_UPDATED.value,
                message=f"Updated mission briefing: {briefing.mission_name}",
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="briefing",
                message=f"Mission briefing updated: {briefing.mission_name}",
            )

            return True

        except Exception as e:
            logger.exception(f"Error updating mission briefing: {e}")
            return False

    @staticmethod
    async def get_mission_status(context: ConversationContext) -> Optional[MissionStatus]:
        """Gets the mission status for the current conversation's mission."""
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            return None

        return MissionStorage.read_mission_status(mission_id)

    @staticmethod
    async def update_mission_status(
        context: ConversationContext,
        state: Optional[str] = None,
        progress: Optional[int] = None,
        status_message: Optional[str] = None,
        next_actions: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[MissionStatus]]:
        """
        Updates the mission status.

        Args:
            context: Current conversation context
            state: Optional mission state
            progress: Optional progress percentage (0-100)
            status_message: Optional status message
            next_actions: Optional list of next actions

        Returns:
            Tuple of (success, mission_status)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot update status: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot update status: no user found in conversation")
                return False, None

            # Get existing status or create new
            status = MissionStorage.read_mission_status(mission_id)
            is_new = False

            if not status:
                # Create new status
                status = MissionStatus(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    active_blockers=[],
                    next_actions=[],
                )

                # Copy goals from briefing if available
                briefing = MissionStorage.read_mission_briefing(mission_id)
                if briefing:
                    status.goals = briefing.goals

                    # Calculate total criteria
                    total_criteria = 0
                    for goal in briefing.goals:
                        total_criteria += len(goal.success_criteria)

                    status.total_criteria = total_criteria

                is_new = True

            # Apply updates
            if state:
                status.state = MissionState(state)

            if progress is not None:
                status.progress_percentage = min(max(progress, 0), 100)

            if status_message:
                status.status_message = status_message

            if next_actions:
                status.next_actions = next_actions

            # Update metadata
            status.updated_at = datetime.utcnow()
            status.updated_by = current_user_id
            status.version += 1

            # Save the status
            MissionStorage.write_mission_status(mission_id, status)

            # Log the update
            event_type = LogEntryType.STATUS_CHANGED
            message = "Created mission status" if is_new else "Updated mission status"

            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=event_type.value,
                message=message,
                metadata={
                    "state": status.state.value if status.state else None,
                    "progress": status.progress_percentage,
                },
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="status",
                message=f"Mission status updated: {status.state.value if status.state else 'Unknown'}",
            )

            return True, status

        except Exception as e:
            logger.exception(f"Error updating mission status: {e}")
            return False, None

    @staticmethod
    async def get_field_requests(context: ConversationContext) -> List[FieldRequest]:
        """Gets all field requests for the current conversation's mission."""
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            return []

        return MissionStorage.get_all_field_requests(mission_id)

    @staticmethod
    async def create_field_request(
        context: ConversationContext,
        title: str,
        description: str,
        priority: RequestPriority = RequestPriority.MEDIUM,
        related_goal_ids: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[FieldRequest]]:
        """
        Creates a new field request.

        Args:
            context: Current conversation context
            title: Title of the request
            description: Description of the request
            priority: Priority level
            related_goal_ids: Optional list of related goal IDs

        Returns:
            Tuple of (success, field_request)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot create field request: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot create field request: no user found in conversation")
                return False, None

            # Create the field request
            field_request = FieldRequest(
                title=title,
                description=description,
                priority=priority,
                related_goal_ids=related_goal_ids or [],
                created_by=current_user_id,
                updated_by=current_user_id,
                conversation_id=str(context.id),
            )

            # Save the request
            MissionStorage.write_field_request(mission_id, field_request)

            # Log the creation
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.REQUEST_CREATED.value,
                message=f"Created field request: {title}",
                related_entity_id=field_request.request_id,
                metadata={"priority": priority.value, "request_id": field_request.request_id},
            )

            # Update mission status to add this request as a blocker if high priority
            if priority in [RequestPriority.HIGH, RequestPriority.CRITICAL]:
                status = MissionStorage.read_mission_status(mission_id)
                if status and field_request.request_id:
                    status.active_blockers.append(field_request.request_id)
                    status.updated_at = datetime.utcnow()
                    status.updated_by = current_user_id
                    status.version += 1
                    MissionStorage.write_mission_status(mission_id, status)

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="field_request",
                message=f"New field request: {title} (Priority: {priority.value})",
            )

            return True, field_request

        except Exception as e:
            logger.exception(f"Error creating field request: {e}")
            return False, None

    @staticmethod
    async def update_field_request(
        context: ConversationContext,
        request_id: str,
        updates: Dict[str, Any],
    ) -> Tuple[bool, Optional[FieldRequest]]:
        """
        Updates an existing field request.

        Args:
            context: Current conversation context
            request_id: ID of the request to update
            updates: Dictionary of fields to update

        Returns:
            Tuple of (success, field_request)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot update field request: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot update field request: no user found in conversation")
                return False, None

            # Get the field request
            field_request = MissionStorage.read_field_request(mission_id, request_id)
            if not field_request:
                logger.error(f"Field request {request_id} not found")
                return False, None

            # Apply updates, skipping protected fields
            updated = False
            protected_fields = ["request_id", "created_by", "created_at", "conversation_id", "version"]

            for field, value in updates.items():
                if hasattr(field_request, field) and field not in protected_fields:
                    # Special handling for status changes
                    if field == "status" and field_request.status != value:
                        # Add an update to the history
                        field_request.updates.append({
                            "timestamp": datetime.utcnow().isoformat(),
                            "user_id": current_user_id,
                            "message": f"Status changed from {field_request.status.value} to {value.value}",
                            "status": value.value,
                        })

                    setattr(field_request, field, value)
                    updated = True

            if not updated:
                logger.info(f"No updates applied to field request {request_id}")
                return True, field_request

            # Update metadata
            field_request.updated_at = datetime.utcnow()
            field_request.updated_by = current_user_id
            field_request.version += 1

            # Save the updated request
            MissionStorage.write_field_request(mission_id, field_request)

            # Log the update
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.REQUEST_UPDATED.value,
                message=f"Updated field request: {field_request.title}",
                related_entity_id=field_request.request_id,
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="field_request_updated",
                message=f"Field request updated: {field_request.title}",
            )

            return True, field_request

        except Exception as e:
            logger.exception(f"Error updating field request: {e}")
            return False, None

    @staticmethod
    async def resolve_field_request(
        context: ConversationContext,
        request_id: str,
        resolution: str,
    ) -> Tuple[bool, Optional[FieldRequest]]:
        """
        Resolves a field request.

        Args:
            context: Current conversation context
            request_id: ID of the request to resolve
            resolution: Resolution information

        Returns:
            Tuple of (success, field_request)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot resolve field request: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot resolve field request: no user found in conversation")
                return False, None

            # Get the field request
            field_request = MissionStorage.read_field_request(mission_id, request_id)
            if not field_request:
                # Try to find it in all requests
                all_requests = MissionStorage.get_all_field_requests(mission_id)
                for request in all_requests:
                    if request.request_id == request_id:
                        field_request = request
                        break

                if not field_request:
                    logger.error(f"Field request {request_id} not found")
                    return False, None

            # Check if already resolved
            if field_request.status == RequestStatus.RESOLVED:
                logger.info(f"Field request {request_id} is already resolved")
                return True, field_request

            # Update the request
            field_request.status = RequestStatus.RESOLVED
            field_request.resolution = resolution
            field_request.resolved_at = datetime.utcnow()
            field_request.resolved_by = current_user_id

            # Add to history
            field_request.updates.append({
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": current_user_id,
                "message": f"Request resolved: {resolution}",
                "status": RequestStatus.RESOLVED.value,
            })

            # Update metadata
            field_request.updated_at = datetime.utcnow()
            field_request.updated_by = current_user_id
            field_request.version += 1

            # Save the updated request
            MissionStorage.write_field_request(mission_id, field_request)

            # Log the resolution
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.REQUEST_RESOLVED.value,
                message=f"Resolved field request: {field_request.title}",
                related_entity_id=field_request.request_id,
                metadata={
                    "resolution": resolution,
                    "request_title": field_request.title,
                    "request_priority": field_request.priority.value
                    if hasattr(field_request.priority, "value")
                    else field_request.priority,
                },
            )

            # Update mission status if this was a blocker
            status = MissionStorage.read_mission_status(mission_id)
            if status and field_request.request_id in status.active_blockers:
                status.active_blockers.remove(field_request.request_id)
                status.updated_at = datetime.utcnow()
                status.updated_by = current_user_id
                status.version += 1
                MissionStorage.write_mission_status(mission_id, status)

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="field_request_resolved",
                message=f"Field request resolved: {field_request.title}",
            )

            # Also send direct notification to requestor's conversation
            if field_request.conversation_id != str(context.id):
                from semantic_workbench_api_model.workbench_model import MessageType, NewConversationMessage

                from .mission import ConversationClientManager

                try:
                    # Get client for requestor's conversation
                    client = ConversationClientManager.get_conversation_client(context, field_request.conversation_id)

                    # Send notification
                    await client.send_messages(
                        NewConversationMessage(
                            content=f"HQ has resolved your request '{field_request.title}': {resolution}",
                            message_type=MessageType.notice,
                        )
                    )
                except Exception as e:
                    logger.warning(f"Could not send direct notification to requestor: {e}")

            return True, field_request

        except Exception as e:
            logger.exception(f"Error resolving field request: {e}")
            return False, None

    @staticmethod
    async def get_mission_log(context: ConversationContext) -> Optional[MissionLog]:
        """Gets the mission log for the current conversation's mission."""
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            return None

        return MissionStorage.read_mission_log(mission_id)

    @staticmethod
    async def add_log_entry(
        context: ConversationContext,
        entry_type: LogEntryType,
        message: str,
        related_entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[MissionLog]]:
        """
        Adds an entry to the mission log.

        Args:
            context: Current conversation context
            entry_type: Type of log entry
            message: Log message
            related_entity_id: Optional ID of a related entity
            metadata: Optional additional metadata

        Returns:
            Tuple of (success, mission_log)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot add log entry: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None
            user_name = "Unknown User"

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    user_name = participant.name
                    break

            if not current_user_id:
                logger.error("Cannot add log entry: no user found in conversation")
                return False, None

            # Create the log entry
            entry = LogEntry(
                entry_type=entry_type,
                message=message,
                user_id=current_user_id,
                user_name=user_name,
                related_entity_id=related_entity_id,
                metadata=metadata or {},
            )

            # Get existing log or create new one
            mission_log = MissionStorage.read_mission_log(mission_id)
            if not mission_log:
                mission_log = MissionLog(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    entries=[],
                )

            # Add the entry
            mission_log.entries.append(entry)

            # Update metadata
            mission_log.updated_at = datetime.utcnow()
            mission_log.updated_by = current_user_id
            mission_log.version += 1

            # Save the log
            MissionStorage.write_mission_log(mission_id, mission_log)

            # Notify linked conversations for significant events
            significant_types = [
                LogEntryType.MISSION_STARTED,
                LogEntryType.MISSION_COMPLETED,
                LogEntryType.MISSION_ABORTED,
                LogEntryType.GOAL_COMPLETED,
                LogEntryType.GATE_PASSED,
            ]

            if entry_type in significant_types:
                await MissionNotifier.notify_mission_update(
                    context=context,
                    mission_id=mission_id,
                    update_type="mission_log",
                    message=f"Mission update: {message}",
                )

            return True, mission_log

        except Exception as e:
            logger.exception(f"Error adding log entry: {e}")
            return False, None

    @staticmethod
    async def get_mission_kb(context: ConversationContext) -> Optional[MissionKB]:
        """Gets the mission knowledge base for the current conversation's mission."""
        mission_id = await MissionManager.get_mission_id(context)
        if not mission_id:
            return None

        return MissionStorage.read_mission_kb(mission_id)

    @staticmethod
    async def add_kb_section(
        context: ConversationContext,
        title: str,
        content: str,
        order: int = 0,
        tags: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[MissionKB]]:
        """
        Adds a section to the mission knowledge base.

        Args:
            context: Current conversation context
            title: Section title
            content: Section content
            order: Optional display order
            tags: Optional tags for categorization

        Returns:
            Tuple of (success, mission_kb)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot add KB section: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot add KB section: no user found in conversation")
                return False, None

            # Get existing KB or create new one
            kb = MissionStorage.read_mission_kb(mission_id)
            is_new = False

            if not kb:
                kb = MissionKB(
                    created_by=current_user_id,
                    updated_by=current_user_id,
                    conversation_id=str(context.id),
                    sections={},
                )
                is_new = True

            # Create the section
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

            # Save the KB
            MissionStorage.write_mission_kb(mission_id, kb)

            # Log the update
            event_type = LogEntryType.KB_UPDATE
            message = f"{'Created' if is_new else 'Updated'} mission knowledge base: added section '{title}'"

            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=event_type.value,
                message=message,
                metadata={"section_id": section.id, "section_title": title},
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="mission_kb",
                message=f"Mission knowledge base updated: added section '{title}'",
            )

            return True, kb

        except Exception as e:
            logger.exception(f"Error adding KB section: {e}")
            return False, None

    @staticmethod
    async def update_kb_section(
        context: ConversationContext,
        section_id: str,
        updates: Dict[str, Any],
    ) -> Tuple[bool, Optional[MissionKB]]:
        """
        Updates a section in the mission knowledge base.

        Args:
            context: Current conversation context
            section_id: ID of the section to update
            updates: Dictionary of fields to update

        Returns:
            Tuple of (success, mission_kb)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot update KB section: no mission associated with this conversation")
                return False, None

            # Get user information
            participants = await context.get_participants()
            current_user_id = None

            for participant in participants.participants:
                if participant.role == "user":
                    current_user_id = participant.id
                    break

            if not current_user_id:
                logger.error("Cannot update KB section: no user found in conversation")
                return False, None

            # Get existing KB
            kb = MissionStorage.read_mission_kb(mission_id)
            if not kb:
                logger.error(f"Cannot update KB section: no KB found for mission {mission_id}")
                return False, None

            # Check if section exists
            if section_id not in kb.sections:
                logger.error(f"Cannot update KB section: section {section_id} not found")
                return False, None

            # Get the section
            section = kb.sections[section_id]

            # Apply updates, skipping protected fields
            updated = False
            protected_fields = ["id"]

            for field, value in updates.items():
                if hasattr(section, field) and field not in protected_fields:
                    setattr(section, field, value)
                    updated = True

            if not updated:
                logger.info(f"No updates applied to KB section {section_id}")
                return True, kb

            # Update section metadata
            section.last_updated = datetime.utcnow()
            section.updated_by = current_user_id

            # Update KB metadata
            kb.updated_at = datetime.utcnow()
            kb.updated_by = current_user_id
            kb.version += 1

            # Save the KB
            MissionStorage.write_mission_kb(mission_id, kb)

            # Log the update
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.KB_UPDATE.value,
                message=f"Updated knowledge base section: '{section.title}'",
                metadata={"section_id": section_id, "section_title": section.title},
            )

            # Notify linked conversations
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="mission_kb",
                message=f"Mission knowledge base updated: section '{section.title}' modified",
            )

            return True, kb

        except Exception as e:
            logger.exception(f"Error updating KB section: {e}")
            return False, None

    @staticmethod
    async def complete_mission(
        context: ConversationContext,
        summary: Optional[str] = None,
    ) -> Tuple[bool, Optional[MissionStatus]]:
        """
        Completes a mission and updates the status.

        Args:
            context: Current conversation context
            summary: Optional summary of mission results

        Returns:
            Tuple of (success, mission_status)
        """
        try:
            # Get mission ID
            mission_id = await MissionManager.get_mission_id(context)
            if not mission_id:
                logger.error("Cannot complete mission: no mission associated with this conversation")
                return False, None

            # Get role - only HQ can complete a mission
            role = await MissionManager.get_mission_role(context)
            if role != MissionRole.HQ:
                logger.error("Only HQ can complete a mission")
                return False, None

            # Update mission status to completed
            status_message = summary if summary else "Mission completed successfully"
            success, status = await MissionManager.update_mission_status(
                context=context,
                state=MissionState.COMPLETED.value,
                progress=100,
                status_message=status_message,
            )

            if not success or not status:
                return False, None

            # Add completion entry to the log
            await MissionStorage.log_mission_event(
                context=context,
                mission_id=mission_id,
                entry_type=LogEntryType.MISSION_COMPLETED.value,
                message=f"Mission completed: {status_message}",
            )

            # Notify linked conversations with emphasis
            await MissionNotifier.notify_mission_update(
                context=context,
                mission_id=mission_id,
                update_type="mission_completed",
                message=f"🎉 MISSION COMPLETED: {status_message}",
            )

            return True, status

        except Exception as e:
            logger.exception(f"Error completing mission: {e}")
            return False, None
