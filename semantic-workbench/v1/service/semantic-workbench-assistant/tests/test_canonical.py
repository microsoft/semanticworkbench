import datetime
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest_httpx import HTTPXMock
from semantic_workbench_api_model import assistant_model
from semantic_workbench_api_model.workbench_model import AssistantServiceRegistration
from semantic_workbench_assistant import canonical, settings


@pytest.fixture()
def canonical_assistant_service() -> FastAPI:
    return canonical.app


@pytest.fixture()
def mock_workbench_service_url(monkeypatch: pytest.MonkeyPatch) -> str:
    workbench_service_url = "http://test-workbench"
    monkeypatch.setattr(settings, "workbench_service_url", workbench_service_url)
    return workbench_service_url


@pytest.fixture()
def mock_assistant_service_response(
    httpx_mock: HTTPXMock, canonical_assistant_service: FastAPI, mock_workbench_service_url: str
):
    assistant_service_id = canonical_assistant_service.extra.get("assistant_service_id") or ""
    httpx_mock.add_response(
        url=f"{mock_workbench_service_url}/assistant-service-registrations/{assistant_service_id}",
        method="PUT",
        json=AssistantServiceRegistration(
            assistant_service_id=assistant_service_id,
            created_by_user_id="",
            created_by_user_name="",
            created_datetime=datetime.datetime.utcnow(),
            assistant_service_url=settings.callback_url,
            name="",
            description="",
            include_in_listing=True,
            api_key_name="",
            assistant_service_online=True,
            assistant_service_online_expiration_datetime=None,
        ).model_dump(mode="json"),
    )


def test_service_init(canonical_assistant_service: FastAPI, mock_assistant_service_response):
    with TestClient(app=canonical_assistant_service):
        pass


def test_create_assistant_put_config(canonical_assistant_service: FastAPI, mock_assistant_service_response):
    with TestClient(app=canonical_assistant_service) as client:
        assistant_id = str(uuid.uuid4())
        assistant_definition = assistant_model.AssistantPutRequestModel(
            assistant_name="test-assistant",
        )
        response = client.put(f"/{assistant_id}", data={"assistant": assistant_definition.model_dump_json()})
        response.raise_for_status()

        response = client.get(f"/{assistant_id}/config")
        response.raise_for_status()

        original_config_state = assistant_model.ConfigResponseModel(**response.json())
        original_config = canonical.ConfigStateModel(**original_config_state.config)

        # check that the default config state is as expected so we can later assert on the
        # partially updated state
        assert original_config.model_dump(mode="json") == {
            "un_annotated_text": "",
            "short_text": "",
            "long_text": "",
            "setting_int": 0,
            "model": {"name": "gpt35turbo"},
            "prompt": {"custom_prompt": "", "temperature": 0.7},
        }

        config = assistant_model.ConfigPutRequestModel(
            config=canonical.ConfigStateModel(
                short_text="test short text - this should update",
                long_text="test long text - this should update",
                prompt=canonical.PromptConfigModel(
                    custom_prompt="test custom prompt - this should update", temperature=0.999999
                ),
            ).model_dump()
        )

        response = client.put(f"/{assistant_id}/config", json=config.model_dump(mode="json"))
        response.raise_for_status()

        updated_config_state = assistant_model.ConfigResponseModel(**response.json())
        updated_config = canonical.ConfigStateModel(**updated_config_state.config)

        assert updated_config.model_dump(mode="json") == {
            "un_annotated_text": "",
            "short_text": "test short text - this should update",
            "long_text": "test long text - this should update",
            "setting_int": 0,
            "model": {"name": "gpt35turbo"},
            "prompt": {"custom_prompt": "test custom prompt - this should update", "temperature": 0.999999},
        }


def test_create_assistant_put_invalid_config(canonical_assistant_service: FastAPI, mock_assistant_service_response):
    with TestClient(app=canonical_assistant_service) as client:
        assistant_id = str(uuid.uuid4())
        assistant_definition = assistant_model.AssistantPutRequestModel(
            assistant_name="test-assistant",
        )

        response = client.put(f"/{assistant_id}", data={"assistant": assistant_definition.model_dump_json()})
        response.raise_for_status()

        response = client.get(f"/{assistant_id}/config")
        response.raise_for_status()

        original_config_state = assistant_model.ConfigResponseModel(**response.json())

        response = client.put(f"/{assistant_id}/config", json={"data": {"invalid_key": "data"}})
        assert response.status_code in [422, 400]

        response = client.get(f"/{assistant_id}/config")
        response.raise_for_status()

        after_config_state = assistant_model.ConfigResponseModel(**response.json())

        assert after_config_state == original_config_state
