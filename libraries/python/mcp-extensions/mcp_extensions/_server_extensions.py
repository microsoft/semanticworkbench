from mcp import (
    ErrorData,
    ListResourcesRequest,
    ListResourcesResult,
    ReadResourceRequest,
    ReadResourceResult,
    ServerSession,
)
from mcp.server.fastmcp import Context
from mcp.types import ReadResourceRequestParams
from pydantic import AnyUrl


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
    Lists all resources that the client has. This is reliant on the client supporting
    the experimental `resources/list` method.
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
