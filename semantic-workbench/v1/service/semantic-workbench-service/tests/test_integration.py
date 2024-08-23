import io
import json
import logging
import re
import time
import uuid

import httpx
import pytest
import semantic_workbench_assistant.canonical
from asgi_lifespan import LifespanManager
from semantic_workbench_api_model import assistant_model, workbench_model
from tests.types import IntegratedServices, MockUser


async def test_flow_create_assistant_update_config(
    integrated_services: IntegratedServices, test_user: MockUser
) -> None:
    async with (
        LifespanManager(integrated_services.workbench_service_app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=integrated_services.workbench_service_app),  # type: ignore
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(integrated_services.canonical_assistant_service_app),
    ):
        resp = await wb_client.get("/assistant-service-registrations")
        resp.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(resp.json())
        assert len(assistant_services.assistant_service_registrations) == 1
        assistant_service = assistant_services.assistant_service_registrations[0]

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=assistant_service.assistant_service_id
            ).model_dump(mode="json"),
        )
        logging.info("POST wb/assistants resp: %s", resp.json())
        resp.raise_for_status()

        assistant = workbench_model.Assistant(**resp.json())
        logging.info("POST wb/assistants resp loaded into model: %s", assistant)

        resp = await wb_client.get(f"/assistants/{assistant.id}")
        logging.info("GET wb/assistant/id resp: %s", resp.json())
        resp.raise_for_status()

        assert resp.json() == json.loads(assistant.model_dump_json())

        config = assistant_model.ConfigPutRequestModel(
            config=semantic_workbench_assistant.canonical.ConfigStateModel(
                readonly_text="test readonly text - this should not get updated",
                short_text="test short text",
                long_text="test long text",
                prompt=semantic_workbench_assistant.canonical.PromptConfigModel(
                    custom_prompt="test custom prompt", temperature=0.999999
                ),
            ).model_dump()
        )
        resp = await wb_client.put(f"/assistants/{assistant.id}/config", json=config.model_dump(mode="json"))
        resp.raise_for_status()


async def test_flow_create_assistant_update_conversation_state(
    integrated_services: IntegratedServices, test_user: MockUser
) -> None:
    async with (
        LifespanManager(integrated_services.workbench_service_app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=integrated_services.workbench_service_app),  # type: ignore
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(integrated_services.canonical_assistant_service_app),
    ):
        resp = await wb_client.get("/assistant-service-registrations")
        resp.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(resp.json())
        assert len(assistant_services.assistant_service_registrations) == 1
        assistant_service = assistant_services.assistant_service_registrations[0]

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=assistant_service.assistant_service_id
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant.model_validate(resp.json())
        logging.info("POST wb/assistants resp loaded into model: %s", assistant)

        resp = await wb_client.get(f"/assistants/{assistant.id}")
        resp.raise_for_status()
        logging.info("GET wb/assistant/id resp: %s", resp.json())

        assert resp.json() == json.loads(assistant.model_dump_json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()
        participant = workbench_model.ConversationParticipant.model_validate(resp.json())
        assert participant.online is True

        resp = await wb_client.get(f"/assistants/{assistant.id}/conversations/{conversation.id}/states")
        resp.raise_for_status()
        logging.info("GET asst/conversations/id/states resp: %s", resp.json())

        states = assistant_model.StateDescriptionListResponseModel(**resp.json())
        logging.info("GET asst/conversations/id/states resp loaded into model: %s", states)

        assert len(states.states) == 1
        assert states.states[0].id == "simple_state"

        resp = await wb_client.get(f"/assistants/{assistant.id}/conversations/{conversation.id}/states/simple_state")
        resp.raise_for_status()
        logging.info("GET asst/conversations/id/states/simple_state resp: %s", resp.json())

        state = assistant_model.StateResponseModel(**resp.json())
        logging.info("GET asst/conversations/id/states/simple_state resp loaded into model: %s", state)

        assert "message" in state.data

        updated_message = f"updated message {uuid.uuid4()}"
        state_update = assistant_model.StatePutRequestModel(
            data=semantic_workbench_assistant.canonical.ConversationState(
                message=updated_message,
            ).model_dump()
        )
        resp = await wb_client.put(
            f"/assistants/{assistant.id}/conversations/{conversation.id}/states/simple_state",
            json=state_update.model_dump(mode="json"),
        )
        resp.raise_for_status()

        resp = await wb_client.get(f"/assistants/{assistant.id}/conversations/{conversation.id}/states/simple_state")
        resp.raise_for_status()
        logging.info("GET asst/conversations/id/states/simple_state resp: %s", resp.json())

        state = assistant_model.StateResponseModel(**resp.json())
        logging.info("GET asst/conversations/id/states/simple_state resp loaded into model: %s", state)

        assert "message" in state.data
        assert state.data["message"] == updated_message


async def test_flow_create_assistant_send_message_receive_resp(
    integrated_services: IntegratedServices, test_user: MockUser
) -> None:
    async with (
        LifespanManager(integrated_services.workbench_service_app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=integrated_services.workbench_service_app),  # type: ignore
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(integrated_services.canonical_assistant_service_app),
    ):
        resp = await wb_client.get("/assistant-service-registrations")
        resp.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(resp.json())
        assert len(assistant_services.assistant_service_registrations) == 1
        assistant_service = assistant_services.assistant_service_registrations[0]

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=assistant_service.assistant_service_id
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant(**resp.json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        resp = await wb_client.post(
            f"/conversations/{conversation.id}/messages",
            json={"content": "hello"},
        )
        resp.raise_for_status()
        logging.info(f"POST wb/conversations/{conversation.id}/messages resp: %s", resp.json())

        attempts = 1
        messages = []
        while attempts <= 10 and len(messages) < 2:
            if attempts > 1:
                time.sleep(0.5)
            attempts += 1

            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            logging.info(f"GET wb/conversations/{conversation.id}/messages resp: %s", resp.json())

            messages_resp = resp.json()

            assert "messages" in messages_resp
            messages = messages_resp["messages"]

        assert len(messages) > 1


async def test_flow_create_assistant_send_message_receive_resp_export_import_assistant(
    integrated_services: IntegratedServices, test_user: MockUser
) -> None:
    async with (
        LifespanManager(integrated_services.workbench_service_app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=integrated_services.workbench_service_app),  # type: ignore
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(integrated_services.canonical_assistant_service_app),
    ):
        resp = await wb_client.get("/assistant-service-registrations")
        resp.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(resp.json())
        assert len(assistant_services.assistant_service_registrations) == 1
        assistant_service = assistant_services.assistant_service_registrations[0]

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=assistant_service.assistant_service_id
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant(**resp.json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        async def send_message_wait_for_response(conversation: workbench_model.Conversation) -> None:
            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            existing_messages = workbench_model.ConversationMessageList.model_validate(resp.json())

            logging.info(f"POST wb/conversations/{conversation.id}/messages resp: %s", resp.json())
            resp = await wb_client.post(
                f"/conversations/{conversation.id}/messages",
                json={"content": "hello"},
            )
            resp.raise_for_status()
            logging.info(f"POST wb/conversations/{conversation.id}/messages resp: %s", resp.json())

            url = f"/conversations/{conversation.id}/messages"
            params = {}
            if existing_messages.messages:
                params = {"after": str(existing_messages.messages[-1].id)}
            attempts = 1
            messages = []
            while attempts <= 10 and len(messages) < 2:
                if attempts > 1:
                    time.sleep(0.5)

                attempts += 1

                resp = await wb_client.get(url, params=params)
                resp.raise_for_status()
                logging.info(f"GET {url} resp: %s", resp.json())

                messages_response = workbench_model.ConversationMessageList.model_validate(resp.json())
                messages = messages_response.messages

            assert len(messages) == 2
            assert messages[0].sender.participant_role == workbench_model.ParticipantRole.user
            assert messages[1].sender.participant_role == workbench_model.ParticipantRole.assistant

        await send_message_wait_for_response(conversation)

        resp = await wb_client.get(f"/assistants/{assistant.id}/export")
        resp.raise_for_status()

        assert resp.headers["content-type"] == "application/zip"
        assert "content-length" in resp.headers
        assert int(resp.headers["content-length"]) > 0

        logging.info("response: %s", resp.content)

        file_io = io.BytesIO(resp.content)

        for import_number in range(1, 3):
            resp = await wb_client.post("/assistants/import", files={"from_export": file_io})
            logging.info("import %s response: %s", import_number, resp.json())
            resp.raise_for_status()
            new_assistant = workbench_model.Assistant.model_validate(resp.json())

            resp = await wb_client.get(f"/assistants/{new_assistant.id}/conversations")
            conversations = workbench_model.ConversationList.model_validate(resp.json())
            new_conversation = conversations.conversations[0]

            resp = await wb_client.get("/assistants")
            logging.info("response: %s", resp.json())
            resp.raise_for_status()
            assistants_response = workbench_model.AssistantList.model_validate(resp.json())
            assistant_count = len(assistants_response.assistants)
            assert assistant_count == import_number + 1

            for index, assistant in enumerate(assistants_response.assistants):
                if index == assistant_count - 1:
                    assert assistant.name == "test-assistant"
                    continue

                # assistants are ordered by created_datetime descending
                assert assistant.name == f"test-assistant ({assistant_count - index - 1})"

            # ensure the new assistant can send and receive messages in the new conversation
            await send_message_wait_for_response(new_conversation)


async def test_flow_create_assistant_send_message_receive_resp_export_import_conversations(
    integrated_services: IntegratedServices, test_user: MockUser
) -> None:
    async with (
        LifespanManager(integrated_services.workbench_service_app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=integrated_services.workbench_service_app),  # type: ignore
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(integrated_services.canonical_assistant_service_app),
    ):
        resp = await wb_client.get("/assistant-service-registrations")
        resp.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(resp.json())
        assert len(assistant_services.assistant_service_registrations) == 1
        assistant_service = assistant_services.assistant_service_registrations[0]

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=assistant_service.assistant_service_id
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())

        assistant = workbench_model.Assistant(**resp.json())

        resp = await wb_client.post("/conversations", json={"title": "test-conversation"})
        resp.raise_for_status()
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        async def send_message_wait_for_response(conversation: workbench_model.Conversation) -> None:
            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            existing_messages = workbench_model.ConversationMessageList.model_validate(resp.json())

            resp = await wb_client.post(
                f"/conversations/{conversation.id}/messages",
                json={"content": "hello"},
            )
            resp.raise_for_status()
            logging.info(f"POST wb/conversations/{conversation.id}/messages resp: %s", resp.json())

            url = f"/conversations/{conversation.id}/messages"
            params = {}
            if existing_messages.messages:
                params = {"after": str(existing_messages.messages[-1].id)}
            attempts = 1
            messages = []
            while attempts <= 10 and len(messages) < 2:
                if attempts > 1:
                    time.sleep(0.5)

                attempts += 1

                resp = await wb_client.get(url, params=params)
                resp.raise_for_status()
                logging.info(f"GET wb/conversations/{conversation.id}/messages resp: %s", resp.json())

                messages_response = workbench_model.ConversationMessageList.model_validate(resp.json())
                messages = messages_response.messages

            assert len(messages) == 2
            assert messages[0].sender.participant_role == workbench_model.ParticipantRole.user
            assert messages[1].sender.participant_role == workbench_model.ParticipantRole.assistant

        await send_message_wait_for_response(conversation)

        resp = await wb_client.get("/conversations/export", params={"id": str(conversation.id)})
        resp.raise_for_status()

        assert resp.headers["content-type"] == "application/zip"
        assert "content-length" in resp.headers
        assert int(resp.headers["content-length"]) > 0

        logging.info("response: %s", resp.content)

        file_io = io.BytesIO(resp.content)

        for import_number in range(1, 3):
            resp = await wb_client.post("/conversations/import", files={"from_export": file_io})
            logging.info("import %s response: %s", import_number, resp.json())
            resp.raise_for_status()
            import_result = workbench_model.ConversationImportResult.model_validate(resp.json())
            assert len(import_result.assistant_ids) == 1
            new_assistant_id = import_result.assistant_ids[0]

            resp = await wb_client.get(f"/assistants/{new_assistant_id}/conversations")
            conversations = workbench_model.ConversationList.model_validate(resp.json())
            new_conversation = conversations.conversations[0]

            resp = await wb_client.get("/assistants")
            logging.info("response: %s", resp.json())
            resp.raise_for_status()

            assistants_response = workbench_model.AssistantList.model_validate(resp.json())
            assistant_count = len(assistants_response.assistants)
            assert assistant_count == import_number + 1

            for index, assistant in enumerate(assistants_response.assistants):
                if index == assistant_count - 1:
                    assert assistant.name == "test-assistant"
                    continue

                # assistants are ordered by created_datetime descending
                assert assistant.name == f"test-assistant ({assistant_count - index - 1})"

            # ensure the new assistant can send and receive messages in the new conversation
            await send_message_wait_for_response(new_conversation)


@pytest.mark.parametrize(
    # spell-checker:ignore dlrow olleh
    "command,command_args,expected_response_content_regex",
    [
        ("/reverse", "hello world", re.compile("dlrow olleh")),
        ("/reverse", "-h", re.compile("usage: /reverse.+", re.DOTALL)),
        ("/reverse", "", re.compile("/reverse: error: .+", re.DOTALL)),
    ],
)
async def test_flow_create_assistant_send_command_message_receive_resp(
    integrated_services: IntegratedServices,
    test_user: MockUser,
    command,
    command_args,
    expected_response_content_regex: re.Pattern,
) -> None:
    async with (
        LifespanManager(integrated_services.workbench_service_app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=integrated_services.workbench_service_app),  # type: ignore
            headers=test_user.authorization_headers,
            base_url="http://test",
        ) as wb_client,
        LifespanManager(integrated_services.canonical_assistant_service_app),
    ):
        resp = await wb_client.get("/assistant-service-registrations")
        resp.raise_for_status()
        assistant_services = workbench_model.AssistantServiceRegistrationList.model_validate(resp.json())
        assert len(assistant_services.assistant_service_registrations) == 1
        assistant_service = assistant_services.assistant_service_registrations[0]

        resp = await wb_client.post(
            "/assistants",
            json=workbench_model.NewAssistant(
                name="test-assistant", assistant_service_id=assistant_service.assistant_service_id
            ).model_dump(mode="json"),
        )
        resp.raise_for_status()
        logging.info("POST wb/assistants resp: %s", resp.json())
        assistant = workbench_model.Assistant.model_validate(resp.json())
        logging.info("assistant: %s", assistant)

        resp = await wb_client.post(
            "/conversations",
            json={"title": "test-assistant"},
        )
        resp.raise_for_status()
        logging.info("POST wb/conversations resp: %s", resp.json())
        conversation = workbench_model.Conversation.model_validate(resp.json())

        resp = await wb_client.put(f"/conversations/{conversation.id}/participants/{assistant.id}", json={})
        resp.raise_for_status()

        command_content = f"{command} {command_args}"
        resp = await wb_client.post(
            f"/conversations/{conversation.id}/messages",
            json={
                "message_type": "command",
                "content_type": "application/json",
                "content": command_content,
            },
        )
        resp.raise_for_status()
        logging.info(f"POST wb/conversations/{conversation.id}/messages resp: %s", resp.json())

        attempts = 1
        messages = []
        while attempts <= 10 and len(messages) < 2:
            if attempts > 1:
                time.sleep(0.5)
            attempts += 1

            resp = await wb_client.get(f"/conversations/{conversation.id}/messages")
            resp.raise_for_status()
            logging.info(f"GET wb/conversations/{conversation.id}/messages resp: %s", resp.json())

            messages_resp = resp.json()

            assert "messages" in messages_resp
            messages = messages_resp["messages"]

        assert len(messages) > 1
        response_message = messages[1]

        assert expected_response_content_regex.fullmatch(response_message["content"])
        assert response_message["message_type"] == "command-response"
