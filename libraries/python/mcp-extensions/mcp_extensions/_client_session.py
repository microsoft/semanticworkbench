from datetime import timedelta
from typing import Annotated, Any, Literal, Protocol

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp import types
from mcp.client.session import (
    ClientResponse,
    ClientSession,
    ListRootsFnT,
    SamplingFnT,
    _default_list_roots_callback,
    _default_sampling_callback,
)
from mcp.shared.context import RequestContext
from mcp.shared.session import BaseSession, RequestResponder
from mcp.shared.version import SUPPORTED_PROTOCOL_VERSIONS
from pydantic import AnyUrl, ConfigDict, UrlConstraints


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
    """Parameters for reading a resource."""

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
        self, context: RequestContext[ClientSession, Any], params: types.WriteResourceRequestParams
    ) -> types.WriteResourceResult | types.ErrorData: ...


async def _default_write_resource_callback(
    context: RequestContext[ClientSession, Any], params: types.WriteResourceRequestParams
) -> types.WriteResourceResult | types.ErrorData:
    return types.ErrorData(
        code=types.INVALID_REQUEST,
        message="Write resource not supported",
    )


class ExtendedServerRequest(
    types.RootModel[
        types.PingRequest
        | types.CreateMessageRequest
        | types.ListRootsRequest
        | types.ListResourcesRequest
        | types.ReadResourceRequest
        | WriteResourceRequest
    ]
):
    pass


class ExtendedClientResult(
    types.RootModel[
        types.EmptyResult
        | types.CreateMessageResult
        | types.ListRootsResult
        | types.ListResourcesResult
        | types.ReadResourceResult
        | WriteResourceResult
    ]
):
    pass


class ExtendedClientSession(
    BaseSession[
        types.ClientRequest,
        types.ClientNotification,
        ExtendedClientResult,
        ExtendedServerRequest,
        types.ServerNotification,
    ]
):
    def __init__(
        self,
        read_stream: MemoryObjectReceiveStream[types.JSONRPCMessage | Exception],
        write_stream: MemoryObjectSendStream[types.JSONRPCMessage],
        read_timeout_seconds: timedelta | None = None,
        sampling_callback: SamplingFnT | None = None,
        list_roots_callback: ListRootsFnT | None = None,
        experimental_resource_callbacks: tuple[ListResourcesFnT, ReadResourceFnT, WriteResourceFnT] | None = None,
    ) -> None:
        super().__init__(
            read_stream,
            write_stream,
            ExtendedServerRequest,
            types.ServerNotification,
            read_timeout_seconds=read_timeout_seconds,
        )
        self._sampling_callback = sampling_callback or _default_sampling_callback
        self._list_roots_callback = list_roots_callback or _default_list_roots_callback
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

    async def send_ping(self) -> types.EmptyResult:
        """Send a ping request."""
        return await self.send_request(
            types.ClientRequest(
                types.PingRequest(
                    method="ping",
                )
            ),
            types.EmptyResult,
        )

    async def send_progress_notification(
        self, progress_token: str | int, progress: float, total: float | None = None
    ) -> None:
        """Send a progress notification."""
        await self.send_notification(
            types.ClientNotification(
                types.ProgressNotification(
                    method="notifications/progress",
                    params=types.ProgressNotificationParams(
                        progressToken=progress_token,
                        progress=progress,
                        total=total,
                    ),
                ),
            )
        )

    async def set_logging_level(self, level: types.LoggingLevel) -> types.EmptyResult:
        """Send a logging/setLevel request."""
        return await self.send_request(
            types.ClientRequest(
                types.SetLevelRequest(
                    method="logging/setLevel",
                    params=types.SetLevelRequestParams(level=level),
                )
            ),
            types.EmptyResult,
        )

    async def list_resources(self) -> types.ListResourcesResult:
        """Send a resources/list request."""
        return await self.send_request(
            types.ClientRequest(
                types.ListResourcesRequest(
                    method="resources/list",
                )
            ),
            types.ListResourcesResult,
        )

    async def list_resource_templates(self) -> types.ListResourceTemplatesResult:
        """Send a resources/templates/list request."""
        return await self.send_request(
            types.ClientRequest(
                types.ListResourceTemplatesRequest(
                    method="resources/templates/list",
                )
            ),
            types.ListResourceTemplatesResult,
        )

    async def read_resource(self, uri: AnyUrl) -> types.ReadResourceResult:
        """Send a resources/read request."""
        return await self.send_request(
            types.ClientRequest(
                types.ReadResourceRequest(
                    method="resources/read",
                    params=types.ReadResourceRequestParams(uri=uri),
                )
            ),
            types.ReadResourceResult,
        )

    async def subscribe_resource(self, uri: AnyUrl) -> types.EmptyResult:
        """Send a resources/subscribe request."""
        return await self.send_request(
            types.ClientRequest(
                types.SubscribeRequest(
                    method="resources/subscribe",
                    params=types.SubscribeRequestParams(uri=uri),
                )
            ),
            types.EmptyResult,
        )

    async def unsubscribe_resource(self, uri: AnyUrl) -> types.EmptyResult:
        """Send a resources/unsubscribe request."""
        return await self.send_request(
            types.ClientRequest(
                types.UnsubscribeRequest(
                    method="resources/unsubscribe",
                    params=types.UnsubscribeRequestParams(uri=uri),
                )
            ),
            types.EmptyResult,
        )

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> types.CallToolResult:
        """Send a tools/call request."""
        return await self.send_request(
            types.ClientRequest(
                types.CallToolRequest(
                    method="tools/call",
                    params=types.CallToolRequestParams(name=name, arguments=arguments),
                )
            ),
            types.CallToolResult,
        )

    async def list_prompts(self) -> types.ListPromptsResult:
        """Send a prompts/list request."""
        return await self.send_request(
            types.ClientRequest(
                types.ListPromptsRequest(
                    method="prompts/list",
                )
            ),
            types.ListPromptsResult,
        )

    async def get_prompt(self, name: str, arguments: dict[str, str] | None = None) -> types.GetPromptResult:
        """Send a prompts/get request."""
        return await self.send_request(
            types.ClientRequest(
                types.GetPromptRequest(
                    method="prompts/get",
                    params=types.GetPromptRequestParams(name=name, arguments=arguments),
                )
            ),
            types.GetPromptResult,
        )

    async def complete(
        self,
        ref: types.ResourceReference | types.PromptReference,
        argument: dict[str, str],
    ) -> types.CompleteResult:
        """Send a completion/complete request."""
        return await self.send_request(
            types.ClientRequest(
                types.CompleteRequest(
                    method="completion/complete",
                    params=types.CompleteRequestParams(
                        ref=ref,
                        argument=types.CompletionArgument(**argument),
                    ),
                )
            ),
            types.CompleteResult,
        )

    async def list_tools(self) -> types.ListToolsResult:
        """Send a tools/list request."""
        return await self.send_request(
            types.ClientRequest(
                types.ListToolsRequest(
                    method="tools/list",
                )
            ),
            types.ListToolsResult,
        )

    async def send_roots_list_changed(self) -> None:
        """Send a roots/list_changed notification."""
        await self.send_notification(
            types.ClientNotification(
                types.RootsListChangedNotification(
                    method="notifications/roots/list_changed",
                )
            )
        )

    async def _received_request(self, responder: RequestResponder[types.ServerRequest, types.ClientResult]) -> None:
        ctx = RequestContext[ClientSession, Any](
            request_id=responder.request_id,
            meta=responder.request_meta,
            session=self,
            lifespan_context=None,
        )

        match responder.request.root:
            # standard requests
            case types.CreateMessageRequest(params=params):
                with responder:
                    response = await self._sampling_callback(ctx, params)
                    client_response = ClientResponse.validate_python(response)
                    await responder.respond(client_response)

            case types.ListRootsRequest():
                with responder:
                    response = await self._list_roots_callback(ctx)
                    client_response = ClientResponse.validate_python(response)
                    await responder.respond(client_response)

            case types.PingRequest():
                with responder:
                    return await responder.respond(types.ClientResult(root=types.EmptyResult()))

            # experimental requests
            case types.ListResourcesRequest():
                with responder:
                    response = await self._list_resources_callback(ctx)
                    client_response = types.ListResourcesResult.model_validate(response)
                    await responder.respond(client_response)

            case types.ReadResourceRequest(params=params):
                with responder:
                    response = await self._read_resource_callback(ctx, params)
                    client_response = types.ReadResourceResult.model_validate(response)
                    await responder.respond(client_response)

            case WriteResourceRequest(params=params):
                with responder:
                    response = await self._write_resource_callback(ctx, params)
                    client_response = WriteResourceResult.model_validate(response)
                    await responder.respond(client_response)

    async def _received_notification(self, notification: types.ServerNotification) -> None:
        """Handle notifications from the server."""
        match notification.root:
            case types.LoggingMessageNotification(params=params):
                await self._logging_callback(params)
            case _:
                pass
