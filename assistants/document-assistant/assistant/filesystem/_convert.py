# Copyright (c) Microsoft. All rights reserved.

import asyncio
import base64
import io
import logging
import pathlib

import pdfplumber
from markitdown import MarkItDown, StreamInfo

logger = logging.getLogger(__name__)


async def bytes_to_str(file_bytes: bytes, filename: str) -> str:
    """
    Convert the content of the file to a string.
    """
    filename_extension = pathlib.Path(filename).suffix.lower().strip(".")

    match filename_extension:
        # handle most common file types using MarkItDown.
        # Note .eml will include the raw html which is very token heavy
        case _ if filename_extension in ["docx", "pptx", "csv", "xlsx", "html", "eml"]:
            return await _markitdown_bytes_to_str(file_bytes, "." + filename_extension)

        case "pdf":
            return await _pdf_bytes_to_str(file_bytes)

        # if the file has an image extension, convert it to a data URI
        case _ if filename_extension in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif"]:
            return _image_bytes_to_str(file_bytes, filename_extension)

        # otherwise assume it's a regular text-based file
        case _:
            try:
                return file_bytes.decode("utf-8")
            except Exception as e:
                return f"The filetype `{filename_extension}` is not supported or the file itself is malformed: {e}"


async def _markitdown_bytes_to_str(file_bytes: bytes, filename_extension: str) -> str:
    """
    Convert a file using MarkItDown defaults.
    """
    with io.BytesIO(file_bytes) as temp:
        result = await asyncio.to_thread(
            MarkItDown(enable_plugins=False).convert,
            source=temp,
            stream_info=StreamInfo(extension=filename_extension),
        )
        text = result.text_content
    return text


async def _pdf_bytes_to_str(file_bytes: bytes, max_pages: int = 25) -> str:
    """
    Convert a PDF file to text.

    Args:
        file_bytes: The raw content of the PDF file.
        max_pages: The maximum number of pages to read from the PDF file.
    """

    def _read_pages() -> str:
        pages = []
        with io.BytesIO(file_bytes) as temp:
            with pdfplumber.open(temp, pages=list(range(1, max_pages + 1, 1))) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    pages.append(page_text)
        return "\n".join(pages)

    return await asyncio.to_thread(_read_pages)


def _image_bytes_to_str(file_bytes: bytes, file_extension: str) -> str:
    """
    Convert an image to a data URI.
    """
    data = base64.b64encode(file_bytes).decode("utf-8")
    image_type = f"image/{file_extension}"
    data_uri = f"data:{image_type};base64,{data}"
    return data_uri
