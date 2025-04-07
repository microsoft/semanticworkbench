import base64
import io
import logging
import urllib.parse
from typing import Any

from mcp import (
    ClientSession,
    ErrorData,
    ListResourcesResult,
    ReadResourceResult,
    Resource,
)
from mcp.shared.context import RequestContext
from mcp.types import (
    BlobResourceContents,
    ReadResourceRequestParams,
    TextResourceContents,
)
from mcp_extensions import WriteResourceRequestParams, WriteResourceResult
from pydantic import AnyUrl
from semantic_workbench_assistant.assistant_app import ConversationContext

logger = logging.getLogger(__name__)

CLIENT_RESOURCE_SCHEME = "client-resource"


class WorkbenchFileClientResourceHandler:
    """
    Handles the `resources/list`, `resources/read` and `resources/write` methods for an MCP client that
    implements our experimental client-resources capability, backed by the files in a workbench
    conversation.
    """

    def __init__(self, context: ConversationContext) -> None:
        self.context = context

    @staticmethod
    def _filename_to_resource_uri(filename: str) -> AnyUrl:
        path = "/".join([urllib.parse.quote(part) for part in filename.split("/")])
        return AnyUrl(f"{CLIENT_RESOURCE_SCHEME}:///{path}")

    @staticmethod
    def _resource_uri_to_filename(uri: AnyUrl) -> str:
        if uri.scheme != CLIENT_RESOURCE_SCHEME:
            raise ValueError(f"Invalid resource URI scheme: {uri.scheme}")
        return urllib.parse.unquote((uri.path or "").lstrip("/"))

    async def handle_list_resources(
        self,
        context: RequestContext[ClientSession, Any],
    ) -> ListResourcesResult | ErrorData:
        try:
            files_response = await self.context.list_files()

            return ListResourcesResult(
                resources=[
                    Resource(
                        uri=self._filename_to_resource_uri(file.filename),
                        name=file.filename.split("/")[-1],
                        size=file.file_size,
                        mimeType=file.content_type,
                    )
                    for file in files_response.files
                ]
            )
        except Exception as e:
            logger.exception("error listing resources")
            return ErrorData(
                code=500,
                message=f"Error listing resources: {str(e)}",
            )

    async def handle_read_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: ReadResourceRequestParams,
    ) -> ReadResourceResult | ErrorData:
        try:
            filename = self._resource_uri_to_filename(params.uri)
            if not filename:
                return ErrorData(
                    code=400,
                    message=f"Invalid resource URI: {params.uri}",
                )

            file_response = await self.context.get_file(filename)
            if file_response is None:
                return ErrorData(
                    code=404,
                    message=f"Resource {params.uri} not found.",
                )

            buffer = io.BytesIO()

            async with self.context.read_file(filename) as reader:
                async for chunk in reader:
                    buffer.write(chunk)

            if file_response.content_type.startswith("text/"):
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=params.uri,
                            mimeType=file_response.content_type,
                            text=buffer.getvalue().decode("utf-8"),
                        )
                    ]
                )

            return ReadResourceResult(
                contents=[
                    BlobResourceContents(
                        uri=self._filename_to_resource_uri(filename),
                        mimeType=file_response.content_type,
                        blob=base64.b64encode(buffer.getvalue()).decode(),
                    )
                ]
            )

        except Exception as e:
            logger.exception("error reading resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error reading resource {params.uri}: {str(e)}",
            )

    async def handle_write_resource(
        self,
        context: RequestContext[ClientSession, Any],
        params: WriteResourceRequestParams,
    ) -> WriteResourceResult | ErrorData:
        try:
            filename = self._resource_uri_to_filename(params.uri)
            if not filename:
                return ErrorData(
                    code=400,
                    message=f"Invalid resource URI: {params.uri}",
                )

            match params.contents:
                case BlobResourceContents():
                    content_bytes = base64.b64decode(params.contents.blob)
                    content_type = params.contents.mimeType or "application/octet-stream"

                case TextResourceContents():
                    content_bytes = params.contents.text.encode("utf-8")
                    content_type = params.contents.mimeType or "text/plain"

            await self.context.write_file(
                filename=filename,
                content_type=content_type,
                file_content=io.BytesIO(content_bytes),
            )

            return WriteResourceResult()

        except Exception as e:
            logger.exception("error writing resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error writing resource {params.uri}: {str(e)}",
            )
