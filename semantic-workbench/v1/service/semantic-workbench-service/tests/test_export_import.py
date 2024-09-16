import io

import sqlmodel
from semantic_workbench_service import db
from semantic_workbench_service.controller import export_import
from semantic_workbench_service.db import DBSettings

from .types import MockUser


async def test_export_import_assistant(db_settings: DBSettings, test_user: MockUser):
    async with db.create_engine(settings=db_settings) as engine, db.create_session(engine) as session:
        await db.bootstrap_db(engine, settings=db_settings)

        user = db.User(
            user_id=test_user.id,
            name=test_user.name,
        )
        session.add(user)

        assistant_service = db.AssistantServiceRegistration(
            assistant_service_id="test",
            assistant_service_url="https://example.com",
            created_by_user_id=test_user.id,
            name="test",
            description="test",
            api_key_name="test",
        )
        session.add(assistant_service)

        assistant = db.Assistant(
            owner_id=test_user.id,
            name="test",
            assistant_service_id=assistant_service.assistant_service_id,
        )
        session.add(assistant)

        await session.flush()

        conversation = db.Conversation(title="test", owner_id=user.user_id)
        session.add(conversation)

        assistant_participant = db.AssistantParticipant(
            conversation_id=conversation.conversation_id,
            assistant_id=assistant.assistant_id,
        )
        session.add(assistant_participant)

        await session.flush()

        in_memory_file = io.BytesIO()

        for line in export_import.export_assistant_file(
            assistant=assistant,
            conversation=conversation,
            messages=[],
            users=[user],
            user_participants=[],
            assistant_participant=assistant_participant,
        ):
            in_memory_file.write(line)

        in_memory_file.seek(0)

        await export_import.import_files(session=session, owner_id=test_user.id, files=[in_memory_file])
        await session.commit()

        result = await session.exec(sqlmodel.select(db.Assistant))
        assistants = result.all()

        assert len(assistants) == 2
        assert assistants[0].assistant_id == assistant.assistant_id

        assert assistants[1].assistant_id != assistant.assistant_id
        assert assistants[1].assistant_service_id == assistant.assistant_service_id
        assert assistants[1].name == assistant.name + " (1)"
        assert assistants[1].owner_id == test_user.id


async def test_export_import_assistant_conversation(db_settings: DBSettings, test_user: MockUser):
    async with db.create_engine(settings=db_settings) as engine, db.create_session(engine) as session:
        await db.bootstrap_db(engine, settings=db_settings)

        user = db.User(
            user_id=test_user.id,
            name=test_user.name,
        )
        session.add(user)

        assistant_service = db.AssistantServiceRegistration(
            assistant_service_id="test",
            assistant_service_url="https://example.com",
            created_by_user_id=test_user.id,
            name="test",
            description="test",
            api_key_name="test",
        )
        session.add(assistant_service)

        assistant_1 = db.Assistant(
            owner_id=test_user.id,
            name="test",
            assistant_service_id=assistant_service.assistant_service_id,
        )
        session.add(assistant_1)

        assistant_2 = db.Assistant(
            owner_id=test_user.id,
            name="test 2",
            assistant_service_id=assistant_service.assistant_service_id,
        )
        session.add(assistant_2)
        await session.flush()

        conversation = db.Conversation(title="test", owner_id=test_user.id)
        session.add(conversation)

        user_participant = db.UserParticipant(
            conversation_id=conversation.conversation_id,
            user_id=test_user.id,
        )
        session.add(user_participant)

        assistant_participant_1 = db.AssistantParticipant(
            conversation_id=conversation.conversation_id,
            assistant_id=assistant_1.assistant_id,
        )
        session.add(assistant_participant_1)

        assistant_participant_2 = db.AssistantParticipant(
            conversation_id=conversation.conversation_id,
            assistant_id=assistant_2.assistant_id,
        )
        session.add(assistant_participant_2)

        message_1 = db.ConversationMessage(
            conversation_id=conversation.conversation_id,
            sender_participant_id=user_participant.user_id,
            sender_participant_role="user",
            content="test-user-message",
            message_type="chat",
            content_type="text/plain",
        )
        session.add(message_1)

        message_2 = db.ConversationMessage(
            conversation_id=conversation.conversation_id,
            sender_participant_id=str(assistant_1.assistant_id),
            sender_participant_role="assistant",
            content="test-assistant-message",
            message_type="chat",
            content_type="text/plain",
        )
        session.add(message_2)

        await session.flush()

        in_memory_file = io.BytesIO()

        # export assistant_1 only
        for line in export_import.export_assistant_file(
            assistant=assistant_1,
            conversation=conversation,
            assistant_participant=assistant_participant_1,
            user_participants=[user_participant],
            users=[user],
            messages=[message_1, message_2],
        ):
            in_memory_file.write(line)

        in_memory_file.seek(0)

        await export_import.import_files(session=session, owner_id=test_user.id, files=[in_memory_file])
        await session.commit()

        result = await session.exec(sqlmodel.select(db.Assistant))
        assistants = result.all()

        assert len(assistants) == 3
        original_assistant_1, original_assistant_2, new_assistant_1 = assistants
        assert original_assistant_1.assistant_id == assistant_1.assistant_id
        assert original_assistant_2.assistant_id == assistant_2.assistant_id

        assert new_assistant_1.assistant_id != assistant_1.assistant_id
        assert new_assistant_1.assistant_service_id == assistant_1.assistant_service_id
        assert new_assistant_1.name == assistant_1.name + " (1)"
        assert new_assistant_1.owner_id == test_user.id

        result = await session.exec(sqlmodel.select(db.Conversation))
        conversations = result.all()

        assert len(conversations) == 2
        original_conversation, new_conversation = conversations
        assert original_conversation.conversation_id == conversation.conversation_id

        result = await session.exec(sqlmodel.select(db.ConversationMessage))
        messages = result.all()

        assert len(messages) == 4
        original_user_message, original_assistant_message, new_user_message, new_assistant_message = messages
        assert original_user_message.conversation_id == conversation.conversation_id
        assert original_assistant_message.conversation_id == conversation.conversation_id
        assert original_user_message.message_id == message_1.message_id
        assert original_assistant_message.message_id == message_2.message_id

        assert new_user_message.conversation_id == new_conversation.conversation_id
        assert new_user_message.content == message_1.content
        assert new_user_message.sender_participant_id == message_1.sender_participant_id

        assert new_assistant_message.conversation_id == new_conversation.conversation_id
        assert new_assistant_message.content == message_2.content
        assert new_assistant_message.sender_participant_id == str(new_assistant_1.assistant_id)
