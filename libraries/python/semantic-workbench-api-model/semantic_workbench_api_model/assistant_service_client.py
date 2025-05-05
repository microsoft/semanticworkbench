# The workbench service is the only consumer of this.

from __future__ import annotations

import types
import urllib.parse
import uuid
from contextlib import asynccontextmanager
from typing import IO, Any, AsyncGenerator, AsyncIterator, Callable, Mapping, Self

import asgi_correlation_id
import hishel
import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from semantic_workbench_api_model.assistant_model import (
    AssistantPutRequestModel,
    ConfigPutRequestModel,
    ConfigResponseModel,
    ConversationPutRequestModel,
    ServiceInfoModel,
    StateDescriptionListResponseModel,
    StatePutRequestModel,
    StateResponseModel,
)
from semantic_workbench_api_model.workbench_model import ConversationEvent

HEADER_API_KEY = "X-API-Key"


# HTTPX transport factory can be overridden to return an ASGI transport for testing
def httpx_transport_factory() -> httpx.AsyncHTTPTransport:
    return httpx.AsyncHTTPTransport(retries=3)


class AuthParams(BaseModel):
    api_key: str

    def to_request_headers(self) -> Mapping[str, str]:
        return {HEADER_API_KEY: urllib.parse.quote(self.api_key)}

    @staticmethod
    def from_request_headers(headers: Mapping[str, str]) -> AuthParams:
        return AuthParams(api_key=headers.get(HEADER_API_KEY) or "")


class AssistantError(HTTPException):
    pass


class AssistantConnectionError(AssistantError):
    def __init__(
        self,
        error: httpx.RequestError | str,
        status_code: int = 424,
    ) -> None:
        match error:
            case str():
                super().__init__(
                    status_code=status_code,
                    detail=error,
                )
            case httpx.RequestError():
                super().__init__(
                    status_code=status_code,
                    detail=(
                        f"Failed to connect to assistant at url {error.request.url}; {error.__class__.__name__}:"
                        f" {error!s}"
                    ),
                )


class AssistantResponseError(AssistantError):
    def __init__(
        self,
        response: httpx.Response,
    ) -> None:
        super().__init__(
            status_code=response.status_code,
            detail=f"Assistant responded with error; response: {response.text}",
        )


class AssistantClient:
    def __init__(self, httpx_client_factory: Callable[[], httpx.AsyncClient]) -> None:
        self._client = httpx_client_factory()

    async def __aenter__(self) -> Self:
        self._client = await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def put_conversation(self, request: ConversationPutRequestModel, from_export: IO[bytes] | None) -> None:
        try:
            http_response = await self._client.put(
                f"/conversations/{request.id}",
                data={"conversation": request.model_dump_json()},
                files={"from_export": from_export} if from_export is not None else None,
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

    async def delete_conversation(self, conversation_id: uuid.UUID) -> None:
        try:
            http_response = await self._client.delete(f"/conversations/{conversation_id}")
            if http_response.status_code == httpx.codes.NOT_FOUND:
                return

        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

    async def post_conversation_event(self, event: ConversationEvent) -> None:
        try:
            http_response = await self._client.post(
                f"/conversations/{event.conversation_id}/events",
                json=event.model_dump(mode="json"),
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

    async def get_config(self) -> ConfigResponseModel:
        try:
            http_response = await self._client.get("/config")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return ConfigResponseModel.model_validate(http_response.json())

    async def put_config(self, updated_config: ConfigPutRequestModel) -> ConfigResponseModel:
        try:
            http_response = await self._client.put("/config", json=updated_config.model_dump(mode="json"))
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return ConfigResponseModel.model_validate(http_response.json())

    @asynccontextmanager
    async def get_exported_data(self) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        try:
            http_response = await self._client.send(self._client.build_request("GET", "/export-data"), stream=True)
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            # streamed responses must be "read" to get the body
            try:
                await http_response.aread()
                raise AssistantResponseError(http_response)
            finally:
                await http_response.aclose()

        try:
            yield http_response.aiter_bytes(1024)
        finally:
            await http_response.aclose()

    @asynccontextmanager
    async def get_exported_conversation_data(
        self,
        conversation_id: uuid.UUID,
    ) -> AsyncGenerator[AsyncIterator[bytes], Any]:
        try:
            http_response = await self._client.send(
                self._client.build_request("GET", f"/conversations/{conversation_id}/export-data"),
                stream=True,
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            # streamed responses must be "read" to get the body
            try:
                await http_response.aread()
                raise AssistantResponseError(http_response)
            finally:
                await http_response.aclose()

        try:
            yield http_response.aiter_bytes(1024)
        finally:
            await http_response.aclose()

    async def get_state_descriptions(self, conversation_id: uuid.UUID) -> StateDescriptionListResponseModel:
        try:
            http_response = await self._client.get(f"/conversations/{conversation_id}/states")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return StateDescriptionListResponseModel.model_validate(http_response.json())

    async def get_state(self, conversation_id: uuid.UUID, state_id: str) -> StateResponseModel:
        try:
            http_response = await self._client.get(f"/conversations/{conversation_id}/states/{state_id}")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return StateResponseModel.model_validate(http_response.json())

    async def put_state(
        self,
        conversation_id: uuid.UUID,
        state_id: str,
        updated_state: StatePutRequestModel,
    ) -> StateResponseModel:
        try:
            http_response = await self._client.put(
                f"/conversations/{conversation_id}/states/{state_id}",
                json=updated_state.model_dump(mode="json"),
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not http_response.is_success:
            raise AssistantResponseError(http_response)

        return StateResponseModel.model_validate(http_response.json())


class AssistantServiceClient:
    def __init__(
        self,
        httpx_client_factory: Callable[[], httpx.AsyncClient],
    ) -> None:
        self._client = httpx_client_factory()

    async def __aenter__(self) -> Self:
        self._client = await self._client.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: types.TracebackType | None = None,
    ) -> None:
        await self._client.__aexit__(exc_type, exc_value, traceback)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def put_assistant(
        self,
        assistant_id: uuid.UUID,
        request: AssistantPutRequestModel,
        from_export: IO[bytes] | None,
    ) -> None:
        try:
            response = await self._client.put(
                f"/{assistant_id}",
                data={"assistant": request.model_dump_json()},
                files={"from_export": from_export} if from_export is not None else None,
            )
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not response.is_success:
            raise AssistantResponseError(response)

    async def delete_assistant(self, assistant_id: uuid.UUID) -> None:
        try:
            response = await self._client.delete(f"/{assistant_id}")
            if response.status_code == httpx.codes.NOT_FOUND:
                return

        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not response.is_success:
            raise AssistantResponseError(response)

    async def get_service_info(self) -> ServiceInfoModel:
        try:
            response = await self._client.get("/")
        except httpx.RequestError as e:
            raise AssistantConnectionError(e) from e

        if not response.is_success:
            raise AssistantResponseError(response)

        return ServiceInfoModel.model_validate(response.json())


class AssistantServiceClientBuilder:
    def __init__(
        self,
        base_url: str,
        api_key: str,
    ) -> None:
        self._base_url = base_url.strip("/")
        self._api_key = api_key

    def _client(self, *additional_paths: str) -> httpx.AsyncClient:
        return hishel.AsyncCacheClient(
            transport=httpx_transport_factory(),
            base_url="/".join([self._base_url, *additional_paths]),
            timeout=httpx.Timeout(5.0, connect=10.0, read=60.0),
            headers={
                **AuthParams(api_key=self._api_key).to_request_headers(),
                asgi_correlation_id.CorrelationIdMiddleware.header_name: urllib.parse.quote(
                    asgi_correlation_id.correlation_id.get() or ""
                ),
            },
            storage=hishel.AsyncFileStorage(),
        )

    def for_service(self) -> AssistantServiceClient:
        return AssistantServiceClient(httpx_client_factory=self._client)

    def for_assistant(self, assistant_id: uuid.UUID) -> AssistantClient:
        return AssistantClient(
            httpx_client_factory=lambda: self._client(str(assistant_id)),
        )
