import base64

from mcp import (
    ErrorData,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    ServerSession,
)
from mcp.server.fastmcp import Context
from mcp.types import BlobResourceContents, ReadResourceRequestParams, TextResourceContents
from pydantic import AnyUrl

from mcp_extensions import WriteResourceRequest, WriteResourceRequestParams, WriteResourceResult


async def list_client_resources(fastmcp_server_context: Context) -> ListResourcesResult | ErrorData:
    """
    Lists all resources that the client has. This is reliant on the client supporting
    the experimental `resources/list` method.
    """
    server_session: ServerSession = fastmcp_server_context.session

    return await server_session.send_request(
        request=ListResourcesRequest(
            method="resources/list",
        ),  # type: ignore - this is an experimental method not explicitly defined in the mcp package
        result_type=ListResourcesResult,
    )


async def read_client_resource(fastmcp_server_context: Context, uri: AnyUrl) -> ReadResourceResult | ErrorData:
    """
    Reads a resource from the client. This is reliant on the client supporting
    the experimental `resources/read` method.
    """
    server_session: ServerSession = fastmcp_server_context.session

    return await server_session.send_request(
        request=ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(
                uri=uri,
            ),
        ),  # type: ignore - this is an experimental method not explicitly defined in the mcp package
        result_type=ReadResourceResult,
    )


async def write_client_resource(
    fastmcp_server_context: Context, uri: AnyUrl, content_type: str, content: bytes
) -> WriteResourceResult | ErrorData:
    """
    Writes a client resource. This is reliant on the client supporting the experimental `resources/write` method.
    """
    server_session: ServerSession = fastmcp_server_context.session

    if content_type.startswith("text/"):
        contents = TextResourceContents(uri=uri, mimeType=content_type, text=content.decode("utf-8"))
    else:
        contents = BlobResourceContents(uri=uri, mimeType=content_type, blob=base64.b64encode(content).decode())

    return await server_session.send_request(
        request=WriteResourceRequest(
            method="resources/write",
            params=WriteResourceRequestParams(
                uri=uri,
                contents=contents,
            ),
        ),  # type: ignore - this is an experimental method not explicitly defined in the mcp package
        result_type=WriteResourceResult,
    )
