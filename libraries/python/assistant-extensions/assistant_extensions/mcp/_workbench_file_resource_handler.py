import base64
import io
import urllib.parse
from typing import Any

from mcp import ClientSession, ErrorData, ListResourcesResult, ReadResourceResult, Resource
from mcp.shared.context import RequestContext
from mcp.types import BlobResourceContents, ReadResourceRequestParams, TextResourceContents
from pydantic import AnyUrl
from semantic_workbench_assistant.assistant_app import ConversationContext


class WorkbenchFileClientResourceHandler:
    """
    Handles the `resources/list` and `resources/read` methods for an MCP client that
    wants to implement our experimental client-resources capability.
    """

    def __init__(self, context: ConversationContext) -> None:
        self.context = context

    async def handle_list_resources(
        self,
        context: RequestContext[ClientSession, Any],
    ) -> ListResourcesResult | ErrorData:
        files_response = await self.context.list_files()

        def filename_to_resource_url(filename: str) -> AnyUrl:
            parts = [urllib.parse.quote(part) for part in filename.split("/")]
            return AnyUrl("client-resource://" + "/".join(parts))

        return ListResourcesResult(
            resources=[
                Resource(
                    uri=filename_to_resource_url(file.filename),
                    name=file.filename.split("/")[-1],
                    size=file.file_size,
                    mimeType=file.content_type,
                )
                for file in files_response.files
            ]
        )

    async def handle_read_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: ReadResourceRequestParams,
    ) -> ReadResourceResult | ErrorData:
        uri = params.uri
        filename = urllib.parse.unquote(str(uri).replace(uri.scheme + "://", ""))

        file_response = await self.context.get_file(filename)
        if file_response is None:
            return ErrorData(
                code=404,
                message=f"Resource {uri} not found.",
            )

        buffer = io.BytesIO()

        try:
            async with self.context.read_file(filename) as reader:
                async for chunk in reader:
                    buffer.write(chunk)

        except Exception as e:
            return ErrorData(
                code=500,
                message=f"Error reading resource {uri}: {str(e)}",
            )

        if file_response.content_type.startswith("text/"):
            return ReadResourceResult(
                contents=[
                    TextResourceContents(
                        uri=uri,
                        mimeType=file_response.content_type,
                        text=buffer.getvalue().decode("utf-8"),
                    )
                ]
            )

        return ReadResourceResult(
            contents=[
                BlobResourceContents(
                    uri=uri,
                    mimeType=file_response.content_type,
                    blob=base64.b64encode(buffer.getvalue()).decode(),
                )
            ]
        )
