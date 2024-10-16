import asyncio
import base64
import io
import logging
import pathlib

import docx2txt
import pdfplumber

logger = logging.getLogger(__name__)


async def bytes_to_str(file_bytes: bytes, filename: str) -> str:
    """
    Convert the content of the file to a string.
    """
    filename_extension = pathlib.Path(filename).suffix.lower().strip(".")

    match filename_extension:
        # if the file has .docx extension, convert it to text
        case "docx":
            return await _docx_bytes_to_str(file_bytes)

        # if the file has .pdf extension, convert it to text
        case "pdf":
            return await _pdf_bytes_to_str(file_bytes)

        # if the file has an image extension, convert it to a data URI
        case _ if filename_extension in ["png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif"]:
            return _image_bytes_to_str(file_bytes, filename_extension)

        # otherwise, try to convert the file to text
        case _:
            return file_bytes.decode("utf-8")


async def _docx_bytes_to_str(file_bytes: bytes) -> str:
    """
    Convert a DOCX file to text.
    """
    with io.BytesIO(file_bytes) as temp:
        text = await asyncio.to_thread(docx2txt.process, docx=temp)
    return text


async def _pdf_bytes_to_str(file_bytes: bytes, max_pages: int = 10) -> str:
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
