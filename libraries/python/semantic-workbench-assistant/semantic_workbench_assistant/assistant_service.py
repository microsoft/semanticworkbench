import asyncio
import logging
import random
from abc import ABC, abstractmethod
from contextlib import AsyncExitStack, asynccontextmanager
from typing import (
    IO,
    Annotated,
    AsyncContextManager,
    AsyncGenerator,
    AsyncIterator,
    Callable,
    NoReturn,
    Optional,
)

import asgi_correlation_id
import backoff
import backoff.types
import httpx
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, ValidationError
from pydantic_core import Url
from semantic_workbench_api_model import (
    assistant_model,
    workbench_model,
    workbench_service_client,
)
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import auth, settings

logger = logging.getLogger(__name__)


def _backoff_success_handler(details: backoff.types.Details) -> None:
    if details["tries"] == 1:
        return
    logger.info(
        "Success after backoff %s(...); tries: %d, elapsed: %.1fs",
        details["target"].__name__,
        details["tries"],
        details["elapsed"],
    )


class FastAPIAssistantService(ABC):
    """
    Base class for implementations of assistant services using FastAPI.
    """

    def __init__(
        self,
        service_id: str,
        service_name: str,
        service_description: str,
        register_lifespan_handler: Callable[[Callable[[], AsyncContextManager[None]]], None],
    ) -> None:
        self._service_id = service_id
        self._service_name = service_name
        self._service_description = service_description

        @asynccontextmanager
        async def lifespan() -> AsyncIterator[None]:
            logger.info(
                "connecting to semantic-workbench-service; workbench_service_url: %s, assistant_service_id: %s, callback_url: %s",
                settings.workbench_service_url,
                self.service_id,
                settings.callback_url,
            )

            async with self.workbench_client.for_service() as service_client:
                # start periodic pings to workbench
                ping_task = asyncio.create_task(
                    self._periodically_ping_semantic_workbench(service_client), name="ping-workbench"
                )

                try:
                    yield

                finally:
                    ping_task.cancel()
                    try:
                        await ping_task
                    except asyncio.CancelledError:
                        pass

        register_lifespan_handler(lifespan)

    async def _periodically_ping_semantic_workbench(
        self, client: workbench_service_client.AssistantServiceAPIClient
    ) -> NoReturn:
        while True:
            try:
                try:
                    await self._ping_semantic_workbench(client)
                except httpx.HTTPError:
                    logger.exception("ping to workbench failed")

                jitter = random.uniform(0, settings.workbench_service_ping_interval_seconds / 2.0)
                await asyncio.sleep(settings.workbench_service_ping_interval_seconds + jitter)

            except Exception:
                logger.exception("unexpected error in ping loop")

    @backoff.on_exception(
        backoff.expo,
        httpx.HTTPError,
        max_time=30,
        logger=logger,
        on_success=_backoff_success_handler,
    )
    async def _ping_semantic_workbench(self, client: workbench_service_client.AssistantServiceAPIClient) -> None:
        try:
            await client.update_registration_url(
                assistant_service_id=self.service_id,
                update=workbench_model.UpdateAssistantServiceRegistrationUrl(
                    name=self.service_name,
                    description=self.service_description,
                    url=Url(settings.callback_url),
                    online_expires_in_seconds=settings.workbench_service_ping_interval_seconds * 2.5,
                ),
            )

        except httpx.HTTPStatusError as e:
            # log additional information for common error cases
            match e.response.status_code:
                case 401:
                    logger.warning(
                        "authentication failed with semantic-workbench service, configured assistant_service_id and/or"
                        " workbench_service_api_key are incorrect; workbench_service_url: %s,"
                        " assistant_service_id: %s, callback_url: %s",
                        settings.workbench_service_url,
                        self.service_id,
                        settings.callback_url,
                    )
                case 404:
                    logger.warning(
                        "configured assistant_service_id does not exist in the semantic-workbench-service;"
                        " workbench_service_url: %s, assistant_service_id: %s, callback_url: %s",
                        settings.workbench_service_url,
                        self.service_id,
                        settings.callback_url,
                    )
            raise

    @property
    def service_id(self) -> str:
        return settings.assistant_service_id if settings.assistant_service_id is not None else self._service_id

    @property
    def service_name(self) -> str:
        return settings.assistant_service_name if settings.assistant_service_name is not None else self._service_name

    @property
    def service_description(self) -> str:
        return (
            settings.assistant_service_description
            if settings.assistant_service_description is not None
            else self._service_description
        )

    @property
    def workbench_client(self) -> workbench_service_client.WorkbenchServiceClientBuilder:
        return workbench_service_client.WorkbenchServiceClientBuilder(
            base_url=str(settings.workbench_service_url),
            assistant_service_id=self.service_id,
            api_key=settings.workbench_service_api_key,
        )

    @abstractmethod
    async def get_service_info(self) -> assistant_model.ServiceInfoModel:
        pass

    @abstractmethod
    async def put_assistant(
        self,
        assistant_id: str,
        assistant: assistant_model.AssistantPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.AssistantResponseModel:
        pass

    @abstractmethod
    async def export_assistant_data(
        self, assistant_id: str
    ) -> StreamingResponse | FileResponse | JSONResponse | BaseModel:
        pass

    @abstractmethod
    async def get_assistant(self, assistant_id: str) -> assistant_model.AssistantResponseModel:
        pass

    @abstractmethod
    async def delete_assistant(self, assistant_id: str) -> None:
        pass

    @abstractmethod
    async def get_config(self, assistant_id: str) -> assistant_model.ConfigResponseModel:
        pass

    @abstractmethod
    async def put_config(
        self, assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        pass

    @abstractmethod
    async def put_conversation(
        self,
        assistant_id: str,
        conversation_id: str,
        conversation: assistant_model.ConversationPutRequestModel,
        from_export: Optional[IO[bytes]] = None,
    ) -> assistant_model.ConversationResponseModel:
        pass

    @abstractmethod
    async def export_conversation_data(
        self,
        assistant_id: str,
        conversation_id: str,
    ) -> StreamingResponse | FileResponse | JSONResponse | BaseModel:
        pass

    @abstractmethod
    async def get_conversation(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.ConversationResponseModel:
        pass

    @abstractmethod
    async def delete_conversation(self, assistant_id: str, conversation_id: str) -> None:
        pass

    @abstractmethod
    async def post_conversation_event(
        self,
        assistant_id: str,
        conversation_id: str,
        event: workbench_model.ConversationEvent,
    ) -> None:
        pass

    @abstractmethod
    async def get_conversation_state_descriptions(
        self, assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        pass

    @abstractmethod
    async def get_conversation_state(
        self, assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        pass

    @abstractmethod
    async def put_conversation_state(
        self,
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        pass


def _assistant_service_api(
    app: FastAPI,
    service: FastAPIAssistantService,
    enable_auth_middleware: bool = True,
):
    """
    Implements API for AssistantService, forwarding requests to AssistantService.
    """

    if enable_auth_middleware:
        app.add_middleware(
            auth.AuthMiddleware, exclude_methods={"OPTIONS"}, exclude_paths=set(settings.anonymous_paths)
        )
    app.add_middleware(asgi_correlation_id.CorrelationIdMiddleware)

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException) -> Response:
        if 500 <= exc.status_code < 600:
            logger.exception(
                "exception in request handler; method: %s, path: %s", request.method, request.url.path, exc_info=exc
            )
        return await http_exception_handler(request, exc)

    @app.get("/", description="Get the description of the assistant service")
    async def get_service_description() -> assistant_model.ServiceInfoModel:
        return await service.get_service_info()

    @app.put(
        "/{assistant_id}",
        description=(
            "Connect an assistant to the workbench, optionally providing exported-data to restore the assistant"
        ),
    )
    async def put_assistant(
        assistant_id: str,
        assistant_json: Annotated[str, Form(alias="assistant")],
        from_export: Annotated[Optional[UploadFile], File(alias="from_export")] = None,
    ) -> assistant_model.AssistantResponseModel:
        try:
            assistant_request = assistant_model.AssistantPutRequestModel.model_validate_json(assistant_json)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())

        if from_export:
            return await service.put_assistant(assistant_id, assistant_request, from_export.file)

        return await service.put_assistant(assistant_id, assistant_request)

    @app.get(
        "/{assistant_id}",
        description="Get an assistant",
    )
    async def get_assistant(assistant_id: str) -> assistant_model.AssistantResponseModel:
        return await service.get_assistant(assistant_id)

    @app.delete(
        "/{assistant_id}",
        description="Delete an assistant",
    )
    async def delete_assistant(assistant_id: str) -> None:
        return await service.delete_assistant(assistant_id)

    @app.get(
        "/{assistant_id}/export-data",
        description="Export all data for this assistant",
    )
    async def export_assistant_data(assistant_id: str) -> Response:
        response = await service.export_assistant_data(assistant_id)
        match response:
            case StreamingResponse() | FileResponse() | JSONResponse():
                return response
            case BaseModel():
                return JSONResponse(jsonable_encoder(response))
            case _:
                raise TypeError(f"Unexpected response type {type(response)}")

    @app.get(
        "/{assistant_id}/config",
        description="Get config for this assistant",
    )
    async def get_config(assistant_id: str) -> assistant_model.ConfigResponseModel:
        return await service.get_config(assistant_id)

    @app.put(
        "/{assistant_id}/config",
        description="Set config for this assistant",
    )
    async def put_config(
        assistant_id: str, updated_config: assistant_model.ConfigPutRequestModel
    ) -> assistant_model.ConfigResponseModel:
        return await service.put_config(assistant_id, updated_config=updated_config)

    @app.put(
        "/{assistant_id}/conversations/{conversation_id}",
        description=(
            "Join an assistant to a workbench conversation, optionally"
            " providing exported-data to restore the conversation"
        ),
    )
    async def put_conversation(
        assistant_id: str,
        conversation_id: str,
        conversation_json: Annotated[str, Form(alias="conversation")],
        from_export: Annotated[Optional[UploadFile], File(alias="from_export")] = None,
    ) -> assistant_model.ConversationResponseModel:
        try:
            conversation = assistant_model.ConversationPutRequestModel.model_validate_json(conversation_json)
        except ValidationError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=e.errors())

        if from_export:
            return await service.put_conversation(assistant_id, conversation_id, conversation, from_export.file)

        return await service.put_conversation(assistant_id, conversation_id, conversation)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}",
        description="Get the status of a conversation",
    )
    async def get_conversation(assistant_id: str, conversation_id: str) -> assistant_model.ConversationResponseModel:
        return await service.get_conversation(assistant_id, conversation_id)

    @app.delete(
        "/{assistant_id}/conversations/{conversation_id}",
        description="Delete a conversation",
    )
    async def delete_conversation(assistant_id: str, conversation_id: str) -> None:
        return await service.delete_conversation(assistant_id, conversation_id)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}/export-data",
        description="Export all data for a conversation",
    )
    async def export_conversation_data(assistant_id: str, conversation_id: str) -> Response:
        response = await service.export_conversation_data(assistant_id=assistant_id, conversation_id=conversation_id)
        match response:
            case StreamingResponse():
                return response
            case FileResponse():
                return response
            case JSONResponse():
                return response
            case BaseModel():
                return JSONResponse(jsonable_encoder(response))
            case _:
                raise TypeError(f"Unexpected response type {type(response)}")

    @app.post(
        "/{assistant_id}/conversations/{conversation_id}/events",
        description="Notify assistant of an event in the conversation",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def post_conversation_event(
        assistant_id: str,
        conversation_id: str,
        event: workbench_model.ConversationEvent,
    ) -> None:
        return await service.post_conversation_event(assistant_id, conversation_id, event)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}/states",
        description="Get the descriptions of the states available for a conversation",
    )
    async def get_conversation_state_descriptions(
        assistant_id: str, conversation_id: str
    ) -> assistant_model.StateDescriptionListResponseModel:
        return await service.get_conversation_state_descriptions(assistant_id, conversation_id)

    @app.get(
        "/{assistant_id}/conversations/{conversation_id}/states/{state_id}",
        description="Get a specific state by id for a conversation",
    )
    async def get_conversation_state(
        assistant_id: str, conversation_id: str, state_id: str
    ) -> assistant_model.StateResponseModel:
        return await service.get_conversation_state(assistant_id, conversation_id, state_id)

    @app.put(
        "/{assistant_id}/conversations/{conversation_id}/states/{state_id}",
        description="Update a specific state by id for a conversation",
    )
    async def put_conversation_state(
        assistant_id: str,
        conversation_id: str,
        state_id: str,
        updated_state: assistant_model.StatePutRequestModel,
    ) -> assistant_model.StateResponseModel:
        return await service.put_conversation_state(assistant_id, conversation_id, state_id, updated_state)


logger = logging.getLogger(__name__)


class FastAPILifespan:
    def __init__(self) -> None:
        self._lifecycle_handlers: list[Callable[[], AsyncContextManager[None]]] = []

    def register_handler(self, handler: Callable[[], AsyncContextManager[None]]) -> None:
        self._lifecycle_handlers.append(handler)

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        async with AsyncExitStack() as stack:
            logger.debug("app lifespan starting up; title: %s, version: %s", app.title, app.version)

            for handler in self._lifecycle_handlers:
                await stack.enter_async_context(handler())

            logger.info("app lifespan started; title: %s, version: %s", app.title, app.version)

            try:
                yield
            finally:
                logger.debug("app lifespan shutting down; title: %s, version: %s", app.title, app.version)

        logger.info("app lifespan shut down; title: %s, version: %s", app.title, app.version)


def create_app(
    factory: Callable[[FastAPILifespan], FastAPIAssistantService],
    enable_auth_middleware: bool = True,
) -> FastAPI:
    """
    Create a FastAPI app for an AssistantService.
    """
    lifespan = FastAPILifespan()
    svc = factory(lifespan)
    app = FastAPI(
        lifespan=lifespan.lifespan,
        title=svc.service_name,
        description=svc.service_description,
        # extra is used to store metadata about the service
        assistant_service_id=svc.service_id,
    )
    _assistant_service_api(app, svc, enable_auth_middleware)
    return app
