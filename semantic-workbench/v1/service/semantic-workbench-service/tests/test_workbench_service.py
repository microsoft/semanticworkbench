import datetime
import io
import json
import logging
import re
import time
import uuid

import httpx
import pytest
import semantic_workbench_api_model.assistant_model as api_model
import semantic_workbench_service
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic_core import Url
from pytest_httpx import HTTPXMock
from semantic_workbench_api_model import workbench_model, workbench_service_client

from .types import MockUser


def test_service_init(workbench_service: FastAPI):
    with TestClient(app=workbench_service):
        pass


id_segment = "[0-9a-f-]+"


def register_assistant_service(client: TestClient) -> workbench_model.AssistantServiceRegistration:
    new_registration = workbench_model.NewAssistantServiceRegistration(
        assistant_service_id=uuid.uuid4().hex,
        name="test-assistant-service",
        description="",
    )
    http_response = client.post("/assistant-service-registrations", json=new_registration.model_dump(mode="json"))
    http_response.raise_for_status()

    registration = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

    update_with_url = workbench_model.UpdateAssistantServiceRegistrationUrl(
        name=new_registration.name,
        description=new_registration.description,
        url=Url("http://testassistantservice"),
        online_expires_in_seconds=60,
    )
    http_response = client.put(
        f"/assistant-service-registrations/{new_registration.assistant_service_id}",
        json=update_with_url.model_dump(mode="json"),
        headers=workbench_service_client.AssistantServiceRequestHeaders(
            assistant_service_id=registration.assistant_service_id,
            api_key=registration.api_key or "",
        ).to_headers(),
    )
    http_response.raise_for_status()

    return registration


def test_create_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        new_assistant = workbench_model.NewAssistant(
            name="test-assistant",
            assistant_service_id=registration.assistant_service_id,
            metadata={"test": "value"},
        )
        http_response = client.post("/assistants", json=new_assistant.model_dump(mode="json"))
        http_response.raise_for_status()

        logging.info("response: %s", http_response.json())

        assistant_response = workbench_model.Assistant.model_validate(http_response.json())
        assert assistant_response.name == new_assistant.name
        assert assistant_response.assistant_service_id == new_assistant.assistant_service_id
        assert assistant_response.metadata == new_assistant.metadata


def test_create_assistant_request_failure(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    httpx_mock.add_exception(httpx.NetworkError("test error"))

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        new_assistant = workbench_model.NewAssistant(
            name="test-assistant",
            assistant_service_id=registration.assistant_service_id,
            metadata={"test": "value"},
        )
        http_response = client.post("/assistants", json=new_assistant.model_dump(mode="json"))

        assert http_response.status_code == 424
        response_body = http_response.json()
        assert "detail" in response_body
        assert re.match(
            r"Failed to connect to assistant at url http://testassistantservice/[0-9a-f-]{36}; NetworkError: test"
            r" error",
            response_body["detail"],
        )


def test_create_conversation(workbench_service: FastAPI, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_conversation = workbench_model.NewConversation(title="test-conversation", metadata={"test": "value"})
        http_response = client.post("/conversations", json=new_conversation.model_dump(mode="json"))
        http_response.raise_for_status()

        logging.info("response: %s", http_response.json())

        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert conversation_response.title == new_conversation.title
        assert conversation_response.metadata == new_conversation.metadata

        http_response = client.get(f"/conversations/{conversation_response.id}")
        http_response.raise_for_status()

        get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert get_conversation_response.title == new_conversation.title
        assert get_conversation_response.metadata == new_conversation.metadata


def test_create_update_conversation(workbench_service: FastAPI, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_conversation = workbench_model.NewConversation(title="test-conversation", metadata={"test": "value"})
        http_response = client.post("/conversations", json=new_conversation.model_dump(mode="json"))
        http_response.raise_for_status()

        conversation_response = workbench_model.Conversation.model_validate(http_response.json())

        updated_title = f"new-title{uuid.uuid4()}"
        updated_metadata = {"test": uuid.uuid4().hex}

        http_response = client.patch(
            f"/conversations/{conversation_response.id}",
            json=workbench_model.UpdateConversation(title=updated_title, metadata=updated_metadata).model_dump(
                mode="json"
            ),
        )
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_response.id}")
        http_response.raise_for_status()

        get_conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        assert get_conversation_response.title == updated_title
        assert get_conversation_response.metadata == updated_metadata


def test_create_assistant_add_to_conversation(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        assistant_response = http_response.json()
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        http_response.raise_for_status()

        http_response = client.get(f"/assistants/{assistant_id}/conversations")
        http_response.raise_for_status()
        assistant_conversations_response = http_response.json()
        assert len(assistant_conversations_response["conversations"]) == 1


def test_create_assistant_add_to_conversation_delete_assistant_retains_participant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="DELETE",
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()

        assistant = workbench_model.Assistant.model_validate(http_response.json())

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()

        conversation = workbench_model.Conversation.model_validate(http_response.json())

        http_response = client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation.id}/participants")
        http_response.raise_for_status()

        participants = workbench_model.ConversationParticipantList.model_validate(http_response.json())

        assert len(participants.participants) == 2
        assert set(p.id for p in participants.participants) == {test_user.id, str(assistant.id)}

        assistant_participant = next(p for p in participants.participants if p.id == str(assistant.id))
        assert assistant_participant.name == assistant.name
        assert assistant_participant.image == assistant.image
        assert assistant_participant.active_participant is True
        assert assistant_participant.online is True

        # update assistant and verify that the participant attributes are updated
        http_response = client.patch(
            f"/assistants/{assistant.id}",
            json=workbench_model.UpdateAssistant(name="new-name", image="foo").model_dump(mode="json"),
        )
        http_response.raise_for_status()

        assistant = workbench_model.Assistant.model_validate(http_response.json())
        assert assistant.name == "new-name"
        assert assistant.image == "foo"

        http_response = client.get(f"/conversations/{conversation.id}/participants")
        http_response.raise_for_status()

        participants = workbench_model.ConversationParticipantList.model_validate(http_response.json())

        assert len(participants.participants) == 2
        assert set(p.id for p in participants.participants) == {test_user.id, str(assistant.id)}

        assistant_participant = next(p for p in participants.participants if p.id == str(assistant.id))
        assert assistant_participant.name == assistant.name
        assert assistant_participant.image == assistant.image
        assert assistant_participant.active_participant is True
        assert assistant_participant.online is True

        # delete assistant and verify that the participant is still in the conversation
        http_response = client.delete(f"/assistants/{assistant.id}")
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation.id}/participants", params={"include_inactive": True})
        http_response.raise_for_status()

        participants = workbench_model.ConversationParticipantList.model_validate(http_response.json())

        assert len(participants.participants) == 2
        assert set(p.id for p in participants.participants) == {test_user.id, str(assistant.id)}

        assistant_participant = next(p for p in participants.participants if p.id == str(assistant.id))
        assert assistant_participant.name == assistant.name
        assert assistant_participant.image == assistant.image
        assert assistant_participant.active_participant is False
        assert assistant_participant.online is False


def test_create_get_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        assistant_response = http_response.json()
        logging.info("response: %s", assistant_response)
        assert "id" in assistant_response
        id = assistant_response["id"]

        http_response = client.get(f"/assistants/{id}")
        http_response.raise_for_status()
        assert http_response.json() == assistant_response

        http_response = client.get("/assistants")
        http_response.raise_for_status()
        assistants_response = http_response.json()
        assert "assistants" in assistants_response
        assert assistants_response["assistants"] == [assistant_response]


def test_create_update_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant",
                assistant_service_id=registration.assistant_service_id,
                metadata={"test": "value"},
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        assistant_response = http_response.json()
        logging.info("response: %s", assistant_response)
        assert "id" in assistant_response
        id = assistant_response["id"]

        updated_name = f"new-name{uuid.uuid4()}"
        updated_metadata = {"test": uuid.uuid4().hex}
        http_response = client.patch(
            f"/assistants/{id}",
            json=workbench_model.UpdateAssistant(name=updated_name, metadata=updated_metadata).model_dump(mode="json"),
        )
        http_response.raise_for_status()

        http_response = client.get(f"/assistants/{id}")
        http_response.raise_for_status()
        assistants_response = workbench_model.Assistant.model_validate(http_response.json())
        assert assistants_response.name == updated_name
        assert assistants_response.metadata == updated_metadata


def test_create_delete_assistant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="DELETE",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="DELETE",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        assistant_response = http_response.json()
        logging.info("response: %s", assistant_response)
        assert "id" in assistant_response
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        http_response.raise_for_status()

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        http_response.raise_for_status()

        http_response = client.delete(f"/assistants/{assistant_id}")
        http_response.raise_for_status()

        http_response = client.get(f"/assistants/{assistant_id}")
        assert http_response.status_code == 404


def test_create_assistant_update_participant(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
    test_user_2: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        assistant_id = http_response.json()["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_id}/participants")
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        participants_response = http_response.json()
        assert "participants" in participants_response
        participants = participants_response["participants"]
        assert len(participants) == 2

        expected_participant_ids = {test_user.id, assistant_id}
        participant_ids = set((p["id"] for p in participants))
        assert participant_ids == expected_participant_ids

        http_response = client.get(f"/conversations/{conversation_id}/participants/{test_user.id}")
        http_response.raise_for_status()
        my_id_participant = http_response.json()

        http_response = client.get(f"/conversations/{conversation_id}/participants/me")
        http_response.raise_for_status()
        me_participant = http_response.json()

        assert my_id_participant == me_participant

        http_response = client.patch(f"/conversations/{conversation_id}/participants/me", json={"status": "testing"})
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_id}/participants/me")
        http_response.raise_for_status()
        updated_me_participant = http_response.json()
        assert updated_me_participant["status"] == "testing"

        me_timestamp = datetime.datetime.fromisoformat(me_participant["status_updated_timestamp"])
        updated_timestamp = datetime.datetime.fromisoformat(updated_me_participant["status_updated_timestamp"])
        assert updated_timestamp > me_timestamp

        # add test_user_2 as participant of test_user's conversation
        http_response = client.put(
            f"/conversations/{conversation_id}/participants/me",
            json={"status": "joining"},
            headers=test_user_2.authorization_headers,
        )
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_id}/participants")
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        participants = http_response.json()["participants"]

        ids = {p["id"] for p in participants}
        assert ids == {assistant_id, test_user.id, test_user_2.id}


@pytest.mark.parametrize("message_type", ["command", "log", "note", "notice"])
def test_create_conversation_send_nonchat_message(
    workbench_service: FastAPI, httpx_mock: HTTPXMock, test_user: MockUser, message_type: str
):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        # create a chat message that should not be returned
        message_content = "message of type chat"
        payload = {"message_type": "chat", "content_type": "text/plain", "content": message_content}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        http_response.raise_for_status()

        message_content = f"message of type {message_type}"
        payload = {"message_type": message_type, "content_type": "text/plain", "content": message_content}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"message_type": message_type})
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["content"] == message_content
        assert message["sender"]["participant_id"] == test_user.id
        assert message["message_type"] == message_type


def test_create_conversation_send_user_message(workbench_service: FastAPI, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        message = http_response.json()
        message_id = message["id"]

        http_response = client.get(f"/conversations/{conversation_id}/messages")
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["content"] == "hello"
        assert message["sender"]["participant_id"] == test_user.id

        http_response = client.get(f"/conversations/{conversation_id}/messages/{message_id}")
        http_response.raise_for_status()
        message_response = http_response.json()
        assert message_response["content"] == "hello"
        assert message_response["sender"]["participant_id"] == test_user.id

        # send chat another message
        payload = {"content": "hello again"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        message = http_response.json()
        message_two_id = message["id"]

        # send a log message
        payload = {"content": "hello again", "message_type": "log"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        message = http_response.json()
        message_log_id = message["id"]

        # get all messages
        http_response = client.get(f"/conversations/{conversation_id}/messages")
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 3
        message = messages[0]
        assert message["content"] == "hello"
        assert message["sender"]["participant_id"] == test_user.id
        assert message["id"] == message_id
        message = messages[1]
        assert message["content"] == "hello again"
        assert message["sender"]["participant_id"] == test_user.id
        assert message["id"] == message_two_id
        message = messages[2]
        assert message["content"] == "hello again"
        assert message["sender"]["participant_id"] == test_user.id
        assert message["id"] == message_log_id

        # limit messages
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"limit": 1})
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["id"] == message_log_id

        # get messages before
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"before": message_two_id})
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["id"] == message_id

        # get messages after
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"after": message_id})
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 2
        message = messages[0]
        assert message["id"] == message_two_id
        message = messages[1]
        assert message["id"] == message_log_id

        # get messages by type
        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"message_type": "chat"})
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 2

        http_response = client.get(f"/conversations/{conversation_id}/messages", params={"message_type": "log"})
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1

        http_response = client.get(
            f"/conversations/{conversation_id}/messages", params={"message_type": ["chat", "log"]}
        )
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 3


def test_create_assistant_send_assistant_message(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        assistant_response = http_response.json()
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        http_response.raise_for_status()

        payload = {"content": "hello", "metadata": {"assistant_id": assistant_id, "generated_by": "test"}}
        assistant_headers = {
            **workbench_service_client.AssistantServiceRequestHeaders(
                assistant_service_id=registration.assistant_service_id,
                api_key=registration.api_key or "",
            ).to_headers(),
            **workbench_service_client.AssistantInstanceRequestHeaders(
                assistant_id=assistant_id,
            ).to_headers(),
        }
        http_response = client.post(
            f"/conversations/{conversation_id}/messages", json=payload, headers=assistant_headers
        )
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_id}/messages")
        http_response.raise_for_status()
        messages_response = http_response.json()
        assert "messages" in messages_response
        messages = messages_response["messages"]
        assert len(messages) == 1
        message = messages[0]
        assert message["content"] == "hello"
        assert message["sender"]["participant_id"] == assistant_id
        assert message["metadata"] == {"assistant_id": assistant_id, "generated_by": "test"}


def test_create_conversation_write_read_delete_file(workbench_service: FastAPI, httpx_mock, test_user: MockUser):
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.get(f"/conversations/{conversation_id}/files")
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        files = http_response.json()["files"]
        assert len(files) == 0

        # write 3 files
        payload = [
            ("files", ("test.txt", "hello world\n", "text/plain")),
            ("files", ("path1/path2/test.html", "<html><body></body></html>\n", "text/html")),
            ("files", ("path1/path2/test.bin", bytes(range(ord("a"), ord("f"))), "application/octet-stream")),
        ]
        http_response = client.put(
            f"/conversations/{conversation_id}/files",
            files=payload,
            # one of them has metadata
            data={"metadata": json.dumps({"path1/path2/test.bin": {"generated_by": "test"}})},
        )
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        files = http_response.json()["files"]
        assert [f["filename"] for f in files] == ["test.txt", "path1/path2/test.html", "path1/path2/test.bin"]
        assert files[2]["metadata"] == {"generated_by": "test"}

        # get the file listing
        http_response = client.get(f"/conversations/{conversation_id}/files")
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        files = http_response.json()["files"]
        assert [f["filename"] for f in files] == ["path1/path2/test.bin", "path1/path2/test.html", "test.txt"]

        # get files by prefix
        http_response = client.get(f"/conversations/{conversation_id}/files", params={"prefix": "path1/path2"})
        http_response.raise_for_status()
        logging.info("response: %s", http_response.json())
        files = http_response.json()["files"]
        assert [f["filename"] for f in files] == ["path1/path2/test.bin", "path1/path2/test.html"]

        # download a file
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt")
        http_response.raise_for_status()
        assert http_response.text == "hello world\n"

        # download another file
        http_response = client.get(f"/conversations/{conversation_id}/files/path1/path2/test.html")
        http_response.raise_for_status()
        assert http_response.text == "<html><body></body></html>\n"

        # re-write test.txt
        payload = [
            ("files", ("test.txt", "hello again\n", "text/plain")),
        ]
        http_response = client.put(f"/conversations/{conversation_id}/files", files=payload)
        http_response.raise_for_status()

        # get all versions
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt/versions")
        http_response.raise_for_status()
        file_versions = http_response.json()
        assert len(file_versions["versions"]) == 2
        assert file_versions["versions"][0]["version"] == 1
        assert file_versions["versions"][1]["version"] == 2

        # get a single version
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt/versions", params={"version": 1})
        http_response.raise_for_status()
        file_versions = http_response.json()
        assert len(file_versions["versions"]) == 1
        assert file_versions["versions"][0]["version"] == 1

        # get the file content for the current version
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt")
        http_response.raise_for_status()
        assert http_response.text == "hello again\n"

        # get the file content for the prior version
        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt", params={"version": 1})
        http_response.raise_for_status()
        assert http_response.text == "hello world\n"

        # delete a file
        http_response = client.delete(f"/conversations/{conversation_id}/files/test.txt")
        http_response.raise_for_status()

        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt")
        assert http_response.status_code == 404

        http_response = client.get(f"/conversations/{conversation_id}/files/test.txt/versions")
        assert http_response.status_code == 404


def test_create_assistant_export_import_data(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/export-data"),
        method="GET",
        json={"data": "assistant test export data"},
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/export-data"),
        method="GET",
        json={"data": "conversation test export data"},
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        assistant_response = http_response.json()
        assistant_id = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id = conversation_response["id"]

        http_response = client.put(f"/conversations/{conversation_id}/participants/{assistant_id}", json={})
        http_response.raise_for_status()

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id}/messages", json=payload)
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()

        http_response = client.get(f"/assistants/{assistant_id}/export")
        http_response.raise_for_status()

        assert http_response.headers["content-type"] == "application/zip"
        assert "content-length" in http_response.headers
        assert int(http_response.headers["content-length"]) > 0

        logging.info("response: %s", http_response.content)

        file_io = io.BytesIO(http_response.content)

        for import_number in range(1, 3):
            http_response = client.post("/assistants/import", files={"from_export": file_io})
            logging.info("response: %s", http_response.json())
            http_response.raise_for_status()

            http_response = client.get("/assistants")
            logging.info("response: %s", http_response.json())
            http_response.raise_for_status()
            assistants_response = http_response.json()
            assert "assistants" in assistants_response
            assistant_count = len(assistants_response["assistants"])
            assert assistant_count == import_number + 1

            for index, assistant in enumerate(assistants_response["assistants"]):
                if index == assistant_count - 1:
                    assert assistant["name"] == "test-assistant"
                    continue

                # assistants are ordered by created_datetime descending
                assert assistant["name"] == f"test-assistant ({assistant_count - index - 1})"


def test_create_assistant_conversations_export_import_conversations(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/export-data"),
        method="GET",
        json={"data": "assistant test export data"},
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/export-data"),
        method="GET",
        json={"data": "conversation test export data"},
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-1",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        assistant_response = http_response.json()
        assistant_id_1 = assistant_response["id"]

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-2",
                assistant_service_id=registration.assistant_service_id,
            ).model_dump(mode="json"),
        )
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()
        assistant_response = http_response.json()
        assistant_id_2 = assistant_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation-1"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id_1 = conversation_response["id"]

        http_response = client.post("/conversations", json={"title": "test-conversation-2"})
        http_response.raise_for_status()
        conversation_response = http_response.json()
        conversation_id_2 = conversation_response["id"]

        # both assistants are in conversation-1
        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_1}", json={})
        http_response.raise_for_status()

        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_2}", json={})
        http_response.raise_for_status()

        # only assistant-1 is in conversation-2
        http_response = client.put(f"/conversations/{conversation_id_2}/participants/{assistant_id_1}", json={})
        http_response.raise_for_status()

        payload = {"content": "hello"}
        http_response = client.post(f"/conversations/{conversation_id_1}/messages", json=payload)
        http_response.raise_for_status()

        http_response = client.post(f"/conversations/{conversation_id_2}/messages", json=payload)
        http_response.raise_for_status()

        # export both conversations
        http_response = client.get("/conversations/export", params={"id": [conversation_id_1, conversation_id_2]})
        http_response.raise_for_status()

        assert http_response.headers["content-type"] == "application/zip"
        assert "content-length" in http_response.headers
        assert int(http_response.headers["content-length"]) > 0

        logging.info("response: %s", http_response.content)

        file_io = io.BytesIO(http_response.content)

        for import_number in range(1, 3):
            http_response = client.post("/conversations/import", files={"from_export": file_io})
            logging.info("response: %s", http_response.json())
            http_response.raise_for_status()

            http_response = client.get("/assistants")
            logging.info("response: %s", http_response.json())
            http_response.raise_for_status()
            assistants_response = http_response.json()
            assert "assistants" in assistants_response
            assistant_count = len(assistants_response["assistants"])
            assert assistant_count == (import_number + 1) * 2

        http_response = client.get("/assistants")
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()

        assistants = workbench_model.AssistantList.model_validate(http_response.json())

        assistants.assistants.sort(key=lambda a: a.name)
        assert assistants.assistants[0].name == "test-assistant-1"
        assert assistants.assistants[1].name == "test-assistant-1 (1)"
        assert assistants.assistants[2].name == "test-assistant-1 (2)"
        assert assistants.assistants[3].name == "test-assistant-2"
        assert assistants.assistants[4].name == "test-assistant-2 (1)"
        assert assistants.assistants[5].name == "test-assistant-2 (2)"

        http_response = client.get("/conversations")
        logging.info("response: %s", http_response.json())
        http_response.raise_for_status()

        conversations = workbench_model.ConversationList.model_validate(http_response.json())
        conversations.conversations.sort(key=lambda c: c.title)

        assert conversations.conversations[0].title == "test-conversation-1"
        assert conversations.conversations[1].title == "test-conversation-1 (1)"
        assert conversations.conversations[2].title == "test-conversation-1 (2)"
        assert conversations.conversations[3].title == "test-conversation-2"
        assert conversations.conversations[4].title == "test-conversation-2 (1)"
        assert conversations.conversations[5].title == "test-conversation-2 (2)"


def test_create_conversations_get_participants(
    workbench_service: FastAPI,
    httpx_mock: HTTPXMock,
    test_user: MockUser,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )
    new_conversation_response = api_model.ConversationResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}"),
        method="PUT",
        json=new_conversation_response.model_dump(),
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}/conversations/{id_segment}/events"),
        method="POST",
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation-1"})
        http_response.raise_for_status()
        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id_1 = conversation_response.id

        http_response = client.post("/conversations", json={"title": "test-conversation-2"})
        http_response.raise_for_status()
        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id_2 = conversation_response.id

        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-1", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        assistant_response = workbench_model.Assistant.model_validate(http_response.json())
        assistant_id_1 = assistant_response.id

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant-2", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        assistant_response = workbench_model.Assistant.model_validate(http_response.json())
        assistant_id_2 = assistant_response.id

        # both assistants are in conversation-1
        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_1}", json={})
        http_response.raise_for_status()

        http_response = client.put(f"/conversations/{conversation_id_1}/participants/{assistant_id_2}", json={})
        http_response.raise_for_status()

        # only assistant-1 is in conversation-2
        http_response = client.put(f"/conversations/{conversation_id_2}/participants/{assistant_id_1}", json={})
        http_response.raise_for_status()

        for conversation_id, participant_ids in {
            conversation_id_1: {str(assistant_id_1), str(assistant_id_2), test_user.id},
            conversation_id_2: {str(assistant_id_1), test_user.id},
        }.items():
            http_response = client.get(f"/conversations/{conversation_id}/participants")
            http_response.raise_for_status()
            participants_response = workbench_model.ConversationParticipantList.model_validate(http_response.json())

            assert {p.id for p in participants_response.participants} == participant_ids

        for assistant_id, conversation_ids in {
            assistant_id_1: {conversation_id_1, conversation_id_2},
            assistant_id_2: {conversation_id_1},
        }.items():
            http_response = client.get(f"/assistants/{assistant_id}/conversations")
            http_response.raise_for_status()
            conversations_response = workbench_model.ConversationList.model_validate(http_response.json())

            assert {c.id for c in conversations_response.conversations} == conversation_ids


@pytest.mark.parametrize(
    "url_template",
    [
        "/conversations/{conversation_id}",
        "/conversations/{conversation_id}/messages",
        "/conversations/{conversation_id}/participants",
    ],
)
def test_conversation_adds_user_participant_on_conversation_gets(
    workbench_service: FastAPI,
    test_user: MockUser,
    test_user_2: MockUser,
    httpx_mock: HTTPXMock,
    url_template,
):
    new_assistant_response = api_model.AssistantResponseModel(
        id="123",
    )
    httpx_mock.add_response(
        url=re.compile(f"http://testassistantservice/{id_segment}"),
        method="PUT",
        json=new_assistant_response.model_dump(),
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        http_response = client.post("/conversations", json={"title": "test-conversation"})
        http_response.raise_for_status()
        conversation_response = workbench_model.Conversation.model_validate(http_response.json())
        conversation_id = conversation_response.id

        registration = register_assistant_service(client)

        http_response = client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=registration.assistant_service_id
            ).model_dump(mode="json"),
        )
        http_response.raise_for_status()
        assistant_response = workbench_model.Assistant.model_validate(http_response.json())

        # ensure user 2 can make get request without failure
        http_response = client.get(
            url_template.format(conversation_id=conversation_id), headers=test_user_2.authorization_headers
        )
        http_response.raise_for_status()

        # ensure assistant request always returns 404
        assistant_headers = {
            **workbench_service_client.AssistantServiceRequestHeaders(
                assistant_service_id=registration.assistant_service_id,
                api_key=registration.api_key or "",
            ).to_headers(),
            **workbench_service_client.AssistantInstanceRequestHeaders(
                assistant_id=assistant_response.id,
            ).to_headers(),
        }
        http_response = client.get(url_template.format(conversation_id=conversation_id), headers=assistant_headers)
        assert http_response.status_code == 404

        # ensure user 2 is a participant
        http_response = client.get(f"/conversations/{conversation_id}/participants")
        http_response.raise_for_status()
        participants_response = workbench_model.ConversationParticipantList.model_validate(http_response.json())
        assert {p.id for p in participants_response.participants} == {test_user.id, test_user_2.id}


def test_create_update_workflow(workbench_service: FastAPI, test_user: MockUser, test_user_2: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_workflow = workbench_model.NewWorkflowDefinition(
            label="",
            start_state_id="",
            states=[],
            conversation_definitions=[],
            assistant_definitions=[],
            transitions=[],
            context_transfer_instruction="",
        )
        http_response = client.post("/workflow-definitions", json=new_workflow.model_dump(mode="json"))
        http_response.raise_for_status()

        created_workflow = workbench_model.WorkflowDefinition.model_validate(http_response.json())
        assert created_workflow.label == ""

        http_response = client.get(f"/workflow-definitions/{created_workflow.id}")
        http_response.raise_for_status()

        retrieved_workflow = workbench_model.WorkflowDefinition.model_validate(http_response.json())

        assert retrieved_workflow == created_workflow

        http_response = client.get("/workflow-definitions")
        http_response.raise_for_status()

        retrieved_workflows = workbench_model.WorkflowDefinitionList.model_validate(http_response.json())

        assert retrieved_workflows.workflow_definitions == [created_workflow]

        updated_workflow = workbench_model.UpdateWorkflowDefinition(
            label="updated",
            start_state_id="",
            states=[],
            conversation_definitions=[],
            assistant_definitions=[],
            transitions=[],
            context_transfer_instruction="",
        )
        http_response = client.patch(
            f"/workflow-definitions/{created_workflow.id}", json=updated_workflow.model_dump(mode="json")
        )

        http_response = client.get(f"/workflow-definitions/{created_workflow.id}")
        http_response.raise_for_status()

        retrieved_workflow = workbench_model.WorkflowDefinition.model_validate(http_response.json())

        assert retrieved_workflow.label == "updated"
        assert retrieved_workflow.label == "updated"


def test_create_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations", json=new_assistant_service.model_dump(mode="json")
        )
        http_response.raise_for_status()

        created_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert created_assistant_service.name == new_assistant_service.name
        assert created_assistant_service.description == new_assistant_service.description
        assert created_assistant_service.created_by_user_id == test_user.id
        assert created_assistant_service.api_key is not None


def test_create_get_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations", json=new_assistant_service.model_dump(mode="json")
        )
        http_response.raise_for_status()

        # get single registration
        http_response = client.get(f"/assistant-service-registrations/{new_assistant_service.assistant_service_id}")
        http_response.raise_for_status()

        assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert assistant_service.name == new_assistant_service.name
        assert assistant_service.description == new_assistant_service.description
        assert assistant_service.created_by_user_id == test_user.id
        # get on single registration returns a mask API key
        assert assistant_service.api_key is not None
        assert assistant_service.api_key.endswith("*" * 10)

        # get all registrations
        http_response = client.get("/assistant-service-registrations")
        http_response.raise_for_status()

        retrieved_assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(
            http_response.json()
        )

        assert len(retrieved_assistant_services.assistant_service_registrations) == 1

        assistant_service = retrieved_assistant_services.assistant_service_registrations[0]
        assert assistant_service.name == new_assistant_service.name
        assert assistant_service.description == new_assistant_service.description
        assert assistant_service.created_by_user_id == test_user.id
        assert assistant_service.api_key is None

        # get registrations owned by user
        http_response = client.get("/assistant-service-registrations", params={"owner_id": "me"})
        http_response.raise_for_status()

        retrieved_assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(
            http_response.json()
        )

        assert len(retrieved_assistant_services.assistant_service_registrations) == 1

        assistant_service = retrieved_assistant_services.assistant_service_registrations[0]
        assert assistant_service.name == new_assistant_service.name
        assert assistant_service.description == new_assistant_service.description
        assert assistant_service.created_by_user_id == test_user.id
        assert assistant_service.api_key is None


def test_create_update_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-nam",
            description="test description",
        )
        http_response = client.post(
            "/assistant-service-registrations", json=new_assistant_service.model_dump(mode="json")
        )
        http_response.raise_for_status()
        assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        update_assistant_service = workbench_model.UpdateAssistantServiceRegistration(
            name="updated-assistant-service",
            description="updated description",
        )
        http_response = client.patch(
            f"/assistant-service-registrations/{assistant_service.assistant_service_id}",
            json=update_assistant_service.model_dump(mode="json", exclude_unset=True),
        )
        http_response.raise_for_status()

        updated_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert updated_assistant_service.name == update_assistant_service.name
        assert updated_assistant_service.description == update_assistant_service.description
        assert updated_assistant_service.api_key is None


def test_create_assistant_service_registration_reset_api_key(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations", json=new_assistant_service.model_dump(mode="json")
        )
        http_response.raise_for_status()

        created_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert created_assistant_service.api_key is not None

        http_response = client.post(
            f"/assistant-service-registrations/{created_assistant_service.assistant_service_id}/api-key"
        )
        http_response.raise_for_status()

        reset_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert reset_assistant_service.api_key is not None
        # NOTE: the api key will not change because the test ApiKeyStore is used


def test_create_delete_assistant_service_registration(workbench_service: FastAPI, test_user: MockUser) -> None:
    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-name",
            description="test description",
        )

        http_response = client.post(
            "/assistant-service-registrations", json=new_assistant_service.model_dump(mode="json")
        )
        http_response.raise_for_status()

        created_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        http_response = client.delete(
            f"/assistant-service-registrations/{created_assistant_service.assistant_service_id}"
        )
        http_response.raise_for_status()

        http_response = client.get("/assistant-service-registrations")
        http_response.raise_for_status()

        retrieved_assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(
            http_response.json()
        )

        assert len(retrieved_assistant_services.assistant_service_registrations) == 0


def test_create_update_assistant_service_registration_url(
    workbench_service: FastAPI, test_user: MockUser, monkeypatch: pytest.MonkeyPatch
) -> None:
    # force continuous checks for assistants going offline
    monkeypatch.setattr(
        semantic_workbench_service.settings.service, "assistant_service_online_check_interval_seconds", 0.1
    )

    with TestClient(app=workbench_service, headers=test_user.authorization_headers) as client:
        new_assistant_service = workbench_model.NewAssistantServiceRegistration(
            assistant_service_id="test-assistant-service-id",
            name="test-assistant-service-nam",
            description="test description",
        )
        http_response = client.post(
            "/assistant-service-registrations", json=new_assistant_service.model_dump(mode="json")
        )
        http_response.raise_for_status()
        assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        update_assistant_service = workbench_model.UpdateAssistantServiceRegistrationUrl(
            name="updated-assistant-service",
            description="updated description",
            url=Url("https://example.com"),
            online_expires_in_seconds=0,
        )
        http_response = client.put(
            f"/assistant-service-registrations/{assistant_service.assistant_service_id}",
            json=update_assistant_service.model_dump(mode="json", exclude_unset=True),
            headers=workbench_service_client.AssistantServiceRequestHeaders(
                assistant_service_id=assistant_service.assistant_service_id,
                api_key=assistant_service.api_key or "",
            ).to_headers(),
        )
        http_response.raise_for_status()

        updated_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert updated_assistant_service.api_key is None
        assert updated_assistant_service.assistant_service_url == str(update_assistant_service.url)
        assert updated_assistant_service.assistant_service_online is True

        # give time for the assistant service online check to run
        time.sleep(1.0)

        # verify that when the url expires, the assistant service is reported as offline
        http_response = client.get(f"/assistant-service-registrations/{assistant_service.assistant_service_id}")
        http_response.raise_for_status()
        retrieved_assistant_service = workbench_model.AssistantServiceRegistration.model_validate(http_response.json())

        assert retrieved_assistant_service.assistant_service_online is False
