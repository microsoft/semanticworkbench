from datetime import timedelta
from typing import Annotated, Any, Literal, Protocol

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import types
from mcp.client.session import (
    ClientSession,
    ListRootsFnT,
    LoggingFnT,
    MessageHandlerFnT,
    SamplingFnT,
)
from mcp.shared.context import RequestContext
from mcp.shared.session import RequestResponder
from mcp.shared.version import SUPPORTED_PROTOCOL_VERSIONS
from pydantic import AnyUrl, ConfigDict, RootModel, TypeAdapter, UrlConstraints


class ListResourcesFnT(Protocol):
    async def __call__(
        self, context: RequestContext[ClientSession, Any]
    ) -> types.ListResourcesResult | types.ErrorData: ...


async def _default_list_resources_callback(
    context: RequestContext[ClientSession, Any],
) -> types.ListResourcesResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="List resources not supported",
    )


class ReadResourceFnT(Protocol):
    async def __call__(
        self, context: RequestContext[ClientSession, Any], params: types.ReadResourceRequestParams
    ) -> types.ReadResourceResult | types.ErrorData: ...


async def _default_read_resource_callback(
    context: RequestContext[ClientSession, Any], params: types.ReadResourceRequestParams
) -> types.ReadResourceResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="Read resource not supported",
    )


class WriteResourceRequestParams(types.RequestParams):
    """Parameters for writing a resource."""

    uri: Annotated[AnyUrl, UrlConstraints(host_required=False)]
    """
    The URI of the resource to write. The URI can use any protocol; it is up to the
    client how to interpret it.
    """
    contents: types.BlobResourceContents | types.TextResourceContents
    """
    The contents of the resource to write. This can be either a blob or text resource.
    """
    model_config = ConfigDict(extra="allow")


class WriteResourceRequest(types.Request):
    """Sent from the server to the client, to write a specific resource URI."""

    method: Literal["resources/write"]
    params: WriteResourceRequestParams


class WriteResourceResult(types.Result):
    """Result of a write resource request."""

    pass


class WriteResourceFnT(Protocol):
    async def __call__(
        self, context: RequestContext[ClientSession, Any], params: WriteResourceRequestParams
    ) -> WriteResourceResult | types.ErrorData: ...


async def _default_write_resource_callback(
    context: RequestContext[ClientSession, Any], params: WriteResourceRequestParams
) -> WriteResourceResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="Write resource not supported",
    )


class ExtendedServerRequest(
    RootModel[
        types.PingRequest
        | types.CreateMessageRequest
        | types.ListRootsRequest
        | types.ListResourcesRequest
        | types.ReadResourceRequest
        | WriteResourceRequest
    ]
):
    pass


class ExtendedClientSession(ClientSession):
    def __init__(
        self,
        read_stream: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception],
        write_stream: MemoryObjectSendStream[types.JSONRPCMessage],
        read_timeout_seconds: timedelta | None = None,
        sampling_callback: SamplingFnT | None = None,
        list_roots_callback: ListRootsFnT | None = None,
        logging_callback: LoggingFnT | None = None,
        message_handler: MessageHandlerFnT | None = None,
        experimental_resource_callbacks: tuple[ListResourcesFnT, ReadResourceFnT, WriteResourceFnT] | None = None,
    ) -> None:
        super().__init__(
            read_stream=read_stream,
            write_stream=write_stream,
            read_timeout_seconds=read_timeout_seconds,
            sampling_callback=sampling_callback,
            list_roots_callback=list_roots_callback,
            logging_callback=logging_callback,
            message_handler=message_handler,
        )
        self._receive_request_type = ExtendedServerRequest
        self._list_resources_callback, self._read_resource_callback, self._write_resource_callback = (
            experimental_resource_callbacks
            or (
                _default_list_resources_callback,
                _default_read_resource_callback,
                _default_write_resource_callback,
            )
        )

    async def initialize(self) -> types.InitializeResult:
        sampling = types.SamplingCapability() if self._sampling_callback is not None else None
        roots = (
            types.RootsCapability(
                # TODO: Should this be based on whether we
                # _will_ send notifications, or only whether
                # they're supported?
                listChanged=True,
            )
            if self._list_roots_callback is not None
            else None
        )
        experimental = {"resources": {}} if self._list_resources_callback is not None else None

        result = await self.send_request(
            types.ClientRequest(
                types.InitializeRequest(
                    method="initialize",
                    params=types.InitializeRequestParams(
                        protocolVersion=types.LATEST_PROTOCOL_VERSION,
                        capabilities=types.ClientCapabilities(
                            sampling=sampling,
                            experimental=experimental,
                            roots=roots,
                        ),
                        clientInfo=types.Implementation(name="mcp", version="0.1.0"),
                    ),
                )
            ),
            types.InitializeResult,
        )

        if result.protocolVersion not in SUPPORTED_PROTOCOL_VERSIONS:
            raise RuntimeError(f"Unsupported protocol version from the server: {result.protocolVersion}")

        await self.send_notification(
            types.ClientNotification(types.InitializedNotification(method="notifications/initialized"))
        )

        return result

    async def _received_request(self, responder: RequestResponder[types.ServerRequest, types.ClientResult]) -> None:
        ctx = RequestContext[ExtendedClientSession, Any](
            request_id=responder.request_id,
            meta=responder.request_meta,
            session=self,
            lifespan_context=None,
        )

        match responder.request.root:
            # "experimental" (non-standard) requests are handled by this class
            case types.ListResourcesRequest():
                with responder:
                    response = await self._list_resources_callback(ctx)
                    client_response = TypeAdapter(types.ListResourcesResult | types.ErrorData).validate_python(response)
                    await responder.respond(client_response)

            case types.ReadResourceRequest(params=params):
                with responder:
                    response = await self._read_resource_callback(ctx, params)
                    client_response = TypeAdapter(types.ReadResourceResult | types.ErrorData).validate_python(response)
                    await responder.respond(client_response)

            case WriteResourceRequest(params=params):
                with responder:
                    response = await self._write_resource_callback(ctx, params)
                    client_response = TypeAdapter(WriteResourceResult | types.ErrorData).validate_python(response)
                    await responder.respond(client_response)

            # standard requests go to ClientSession
            case _:
                return await super()._received_request(responder)
