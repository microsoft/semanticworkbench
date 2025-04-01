import base64
import io
import logging
import urllib.parse
from typing import Any, Awaitable, Callable

from assistant_drive import Drive, IfDriveFileExistsBehavior
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
from semantic_workbench_assistant.assistant_app.context import ConversationContext

logger = logging.getLogger(__name__)

CLIENT_RESOURCE_SCHEME = "client-resource"


class AssistantFileResourceHandler:
    """
    Handles the `resources/list`, `resources/read` and `resources/write` methods for an MCP client that
    implements our experimental client-resources capability, backed by the files in assistant storage.
    """

    def __init__(
        self,
        context: ConversationContext,
        drive: Drive,
        onwrite: Callable[[ConversationContext, str], Awaitable] | None = None,
    ) -> None:
        self._context = context
        self._drive = drive
        self._onwrite = onwrite

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
            resources: list[Resource] = []

            for filename in self._drive.list():
                metadata = self._drive.get_metadata(filename)
                resources.append(
                    Resource(
                        uri=self._filename_to_resource_uri(filename),
                        name=filename,
                        size=metadata.size,
                        mimeType=metadata.content_type,
                    )
                )

            return ListResourcesResult(resources=resources)
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

            try:
                metadata = self._drive.get_metadata(filename)
            except FileNotFoundError:
                return ErrorData(
                    code=404,
                    message=f"Resource {params.uri} not found.",
                )

            buffer = io.BytesIO()
            try:
                with self._drive.open_file(filename) as file:
                    buffer.write(file.read())
            except FileNotFoundError:
                return ErrorData(
                    code=404,
                    message=f"Resource {params.uri} not found.",
                )

            if metadata.content_type.startswith("text/"):
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=self._filename_to_resource_uri(filename),
                            mimeType=metadata.content_type,
                            text=buffer.getvalue().decode("utf-8"),
                        )
                    ]
                )

            return ReadResourceResult(
                contents=[
                    BlobResourceContents(
                        uri=self._filename_to_resource_uri(filename),
                        mimeType=metadata.content_type,
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
                    content_type = (
                        params.contents.mimeType or "application/octet-stream"
                    )

                case TextResourceContents():
                    content_bytes = params.contents.text.encode("utf-8")
                    content_type = params.contents.mimeType or "text/plain"

            self._drive.write(
                filename=filename,
                content_type=content_type,
                content=io.BytesIO(content_bytes),
                if_exists=IfDriveFileExistsBehavior.OVERWRITE,
            )

            if self._onwrite:
                await self._onwrite(self._context, filename)

            return WriteResourceResult()

        except Exception as e:
            logger.exception("error writing resource; uri: %s", params.uri)
            return ErrorData(
                code=500,
                message=f"Error writing resource {params.uri}: {str(e)}",
            )
