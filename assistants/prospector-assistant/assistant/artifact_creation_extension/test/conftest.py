import tempfile
from typing import Iterable
from unittest.mock import AsyncMock, MagicMock, Mock

import dotenv
import openai_client
import pytest
from assistant.artifact_creation_extension import store
from assistant.artifact_creation_extension.config import LLMConfig
from assistant.artifact_creation_extension.extension import LLMs
from openai.types.chat import ChatCompletionReasoningEffort
from pydantic import HttpUrl
from semantic_workbench_assistant import logging_config, settings, storage
from semantic_workbench_assistant.assistant_app.context import AssistantContext, ConversationContext

logging_config.config(settings=settings.logging)


@pytest.fixture(autouse=True, scope="function")
def assistant_settings(monkeypatch: pytest.MonkeyPatch) -> Iterable[None]:
    """Fixture that sets up a temporary directory for the assistant storage."""
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr(settings, "storage", storage.FileStorageSettings(root=temp_dir))
        yield


@pytest.fixture
def assistant_context() -> AssistantContext:
    """Fixture that provides an assistant context for tests."""
    return AssistantContext(
        id="test",
        name="test-assistant",
        _assistant_service_id="test",
    )


@pytest.fixture
def mock_conversation_context(assistant_context: AssistantContext) -> Mock:
    """Fixture that provides a mock conversation context for tests."""
    mock_context = Mock(spec=ConversationContext)
    mock_context.id = "test"
    mock_context.title = "test-conversation"
    mock_context.assistant = assistant_context
    mock_context.set_status = MagicMock()
    mock_context.state_updated_event_after = MagicMock()
    mock_context.send_messages = AsyncMock()

    from assistant.artifact_creation_extension.extension import current_context

    current_context.set(mock_context)

    return mock_context


@pytest.fixture
def llms() -> LLMs:
    """Fixture that provides LLM configurations for tests."""

    endpoint_env_var = dotenv.dotenv_values().get("ASSISTANT__AZURE_OPENAI_ENDPOINT") or ""
    if not endpoint_env_var:
        pytest.skip("ASSISTANT__AZURE_OPENAI_ENDPOINT not set")

    def build_llm_config(
        deployment: str,
        model: str,
        max_response_tokens: int = 16_000,
        reasoning_effort: ChatCompletionReasoningEffort | None = None,
    ) -> LLMConfig:
        """Build LLM configuration for the specified deployment and model."""
        return LLMConfig(
            openai_client_factory=lambda: openai_client.create_client(
                openai_client.AzureOpenAIServiceConfig(
                    auth_config=openai_client.AzureOpenAIAzureIdentityAuthConfig(),
                    azure_openai_endpoint=HttpUrl(endpoint_env_var),
                    azure_openai_deployment=deployment,
                )
            ),
            openai_model=model,
            max_response_tokens=max_response_tokens,
            reasoning_effort=reasoning_effort,
        )

    return LLMs(
        fast=build_llm_config("gpt-4o-mini", "gpt-4o-mini"),
        chat=build_llm_config("gpt-4o", "gpt-4o"),
        reasoning_fast=build_llm_config("o3-mini", "o3-mini", max_response_tokens=50_000, reasoning_effort="low"),
        reasoning_long=build_llm_config("o3-mini", "o3-mini", max_response_tokens=50_000, reasoning_effort="high"),
    )


@pytest.fixture(autouse=True, scope="function")
def document_store(mock_conversation_context: Mock) -> store.DocumentStore:
    """Fixture that provides a document store for tests."""
    document_store = store.for_context(mock_conversation_context)

    from assistant.artifact_creation_extension import tools

    tools.current_document_store.set(document_store)

    return document_store
