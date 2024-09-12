import asyncio
from typing import Self
import uuid
from semantic_workbench_api_model.assistant_service_client import (
    AssistantInstanceClient,
    AssistantServiceClient,
    AssistantServiceClientBuilder,
)
from .. import assistant_api_key, db


class AssistantServiceClientPool:

    def __init__(self, api_key_store: assistant_api_key.ApiKeyStore) -> None:
        self._api_key_store = api_key_store
        self._service_clients: dict[str, AssistantServiceClient] = {}
        self._assistant_clients: dict[uuid.UUID, AssistantInstanceClient] = {}
        self._client_lock = asyncio.Lock()

    def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        for client in self._service_clients.values():
            await client.aclose()
        for client in self._assistant_clients.values():
            await client.aclose()

    async def service_client(self, registration: db.AssistantServiceRegistration) -> AssistantServiceClient:
        service_id = registration.assistant_service_id

        if service_id not in self._service_clients:
            async with self._client_lock:
                if service_id not in self._service_clients:
                    self._service_clients[service_id] = (await self._client_builder(registration)).for_service()

        return self._service_clients[service_id]

    async def assistant_instance_client(self, assistant: db.Assistant) -> AssistantInstanceClient:
        assistant_id = assistant.assistant_id

        if assistant_id not in self._assistant_clients:
            async with self._client_lock:
                if assistant_id not in self._assistant_clients:
                    self._assistant_clients[assistant_id] = (
                        await self._client_builder(assistant.related_assistant_service_registration)
                    ).for_assistant_instance(assistant_id)

        return self._assistant_clients[assistant_id]

    async def _client_builder(
        self,
        registration: db.AssistantServiceRegistration,
    ) -> AssistantServiceClientBuilder:
        api_key = await self._api_key_store.get(registration.api_key_name)
        if api_key is None:
            raise RuntimeError(f"assistant service {registration.assistant_service_id} does not have API key set")

        return AssistantServiceClientBuilder(
            base_url=str(registration.assistant_service_url),
            api_key=api_key,
        )
