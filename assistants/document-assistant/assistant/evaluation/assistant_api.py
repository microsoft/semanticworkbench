# Copyright (c) Microsoft. All rights reserved.

"""
Wraps aspects of the workbench and assistant APIs to make it easy to interact with them at the level we need here.
"""

import asyncio
import base64
import json
import sqlite3
import time
from pathlib import Path

from dotenv import load_dotenv
from semantic_workbench_api_model.workbench_model import (
    Assistant,
    ConversationMessage,
    ConversationParticipant,
    MessageType,
    NewConversation,
    NewConversationMessage,
    ParticipantRole,
    UpdateParticipant,
)
from semantic_workbench_api_model.workbench_service_client import (
    ConversationAPIClient,
    UserRequestHeaders,
    WorkbenchServiceUserClientBuilder,
)

load_dotenv()


def get_user_from_workbench_db() -> tuple[str, str]:
    """Get the user_id and user_name from the local workbench.db file.

    Returns:
        Tuple of (user_id, user_name) for the first user that is not 'semantic-workbench'
    """
    db_path = Path(__file__).parents[4] / "workbench-service" / ".data" / "workbench.db"

    if not db_path.exists():
        raise FileNotFoundError(f"Workbench database not found at {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name FROM user WHERE user_id != 'semantic-workbench' LIMIT 1")
        result = cursor.fetchone()
        if result is None:
            raise ValueError("No non-service users found in the workbench database")
        return result[0], result[1]
    finally:
        conn.close()


def create_test_jwt_token(user_id: str | None = None, user_name: str | None = None) -> str:
    """Create a JWT token for testing (signature verification is disabled in dev mode).

    Args:
        user_id: Database user_id in format "tenant_id.object_id" (defaults to first user from workbench.db)
        user_name: Display name for the user (defaults to first user from workbench.db)
    """
    # Get user info from database if not provided
    if user_id is None or user_name is None:
        try:
            db_user_id, db_user_name = get_user_from_workbench_db()
            if user_id is None:
                user_id = db_user_id
            if user_name is None:
                user_name = db_user_name
        except (FileNotFoundError, ValueError):
            # Fall back to defaults if database is not available
            if user_id is None:
                user_id = "test-tenant-id.test-object-id"
            if user_name is None:
                user_name = "Test User"
    # Split user_id into tenant_id and object_id (format: "tenant.object")
    if "." in user_id:
        tenant_id, object_id = user_id.split(".", 1)
    else:
        # If no dot, treat as object_id with default tenant
        tenant_id = "test-tenant-id"
        object_id = user_id

    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "tid": tenant_id,
        "oid": object_id,
        "name": user_name,
        "appid": "22cb77c3-ca98-4a26-b4db-ac4dcecba690",  # Must match workbench config
    }

    # Create unsigned JWT (signature verification disabled in dev mode)
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = "fake-signature"
    return f"{header_b64}.{payload_b64}.{signature}"


async def get_assistant(client_builder: WorkbenchServiceUserClientBuilder, name: str) -> Assistant | None:
    assistants_client = client_builder.for_assistants()
    assistants = await assistants_client.list_assistants()
    for assistant in assistants.assistants:
        if assistant.name == name:
            return assistant
    return None


async def get_assistant_participant(conversation_client: ConversationAPIClient) -> ConversationParticipant | None:
    """Find the first participant with role = ParticipantRole.assistant.

    Args:
        conversation_client: The conversation API client

    Returns:
        The first assistant participant found, or None if no assistant exists
    """
    participants = await conversation_client.get_participants(include_inactive=True)
    for participant in participants.participants:
        if participant.role == ParticipantRole.assistant:
            return participant
    return None


async def poll_assistant_status(conversation_client: ConversationAPIClient):
    """Polls the assistant status until it finishes responding."""
    # TODO: Wait a bit by blocking. There is some race condition this helps with.
    time.sleep(1)
    while True:
        participant = await get_assistant_participant(conversation_client)
        time.sleep(1)
        participant = await get_assistant_participant(conversation_client)
        if participant and participant.status:
            pass
        else:
            break
        await asyncio.sleep(0.5)


async def get_all_messages(
    conversation_client: ConversationAPIClient,
    message_types: list[MessageType] | None = None,
    participant_role: ParticipantRole | None = None,
) -> list[ConversationMessage]:
    """Get all messages from a conversation by handling pagination.

    Args:
        conversation_client: The conversation API client
        message_types: Optional list of message types to filter by (defaults to all types)
        participant_role: Optional participant role to filter by

    Returns:
        List of all messages in chronological order (oldest first, newest last)
    """
    all_messages: list[ConversationMessage] = []
    before_id = None

    if message_types is None:
        message_types = [
            MessageType.chat,
            MessageType.command,
            MessageType.command_response,
            MessageType.log,
            MessageType.note,
            MessageType.notice,
        ]

    while True:
        message_list = await conversation_client.get_messages(
            before=before_id,
            message_types=message_types,
            participant_role=participant_role,
            limit=100,
        )
        if not message_list.messages:
            break
        all_messages.extend(message_list.messages)
        before_id = message_list.messages[0].id
    return all_messages


async def duplicate_conversation(
    conversation_client: ConversationAPIClient,
    new_title: str,
) -> str:
    """Duplicate a conversation and return the new conversation ID.
    new_conversation_obj = NewConversation(title=new_title)
    new_conversation = await conversation_client.duplicate_conversation(
        new_conversation=new_conversation_obj,
    )
    # Get the first result
    if len(new_conversation.conversation_ids) == 0:
        raise ValueError("No conversation was created during duplication")
    conversation_id = new_conversation.conversation_ids[0]
    return str(conversation_id)
    """
    raise NotImplementedError("Conversation duplication is not implemented yet due to an auth issue.")


if __name__ == "__main__":
    # End to end usage example
    async def main() -> None:
        client_builder = WorkbenchServiceUserClientBuilder(
            base_url="http://127.0.0.1:3000",
            headers=UserRequestHeaders(token=create_test_jwt_token()),
        )

        # Get assistant
        assistant = await get_assistant(client_builder, "Document Assistant 6-13 v1")
        if assistant is None:
            raise ValueError("Assistant not found")

        # Create conversation
        conversations_client = client_builder.for_conversations()
        conversation = await conversations_client.create_conversation(
            NewConversation(title="1 - SERVICE CREATED CONVERSATION")
        )

        # Add assistant to conversation
        conversation_client = client_builder.for_conversation(str(conversation.id))
        await conversation_client.update_participant(
            participant_id=str(assistant.id),
            participant=UpdateParticipant(active_participant=True),
        )

        # This polling is to prevent a race condition where the status has not updated yet.
        await poll_assistant_status(conversation_client)

        # Send a message to the assistant
        await conversation_client.send_messages(NewConversationMessage(content="Hello, assistant!"))

        await poll_assistant_status(conversation_client)

        all_messages = await get_all_messages(conversation_client)
        print(f"Total messages in conversation: {len(all_messages)}")

    asyncio.run(main())
