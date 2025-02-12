from typing import Optional
from pydantic_ai import RunContext
from ..utils.mdconvert import MarkdownConverter

def create_text_inspector_tool(model, text_limit: int):
    """
    Factory function to create the inspect_file_as_text tool.

    This tool reads a file as markdown text and, if a question is provided,
    uses an LLM to generate a caption or answer based on the file's content.

    It handles file extensions: [".html", ".htm", ".xlsx", ".pptx", ".wav", ".mp3",
    ".flac", ".pdf", ".docx"] and all other types of text files.
    IT DOES NOT HANDLE IMAGES (for images, use the visualizer tool instead).

    Args:
        model: An LLM model instance with a `run()` method that accepts a list of messages.
               The call should return an object with a `content` attribute.
        text_limit: Maximum number of characters from the file content to include in prompts.

    Returns:
        An async function that implements the inspect_file_as_text tool.
    """
    md_converter = MarkdownConverter()

    async def inspect_file_as_text(
        ctx: RunContext,
        file_path: str,
        question: Optional[str] = None,
        mode: Optional[str] = "forward"
    ) -> str:
        """
        Read a file as markdown text and optionally answer a question about its content.

        Args:
            file_path: The path to the file you want to inspect (e.g. '.pdf', '.docx', etc.).
                       Must be a '.something' file. If the file is an image (e.g. '.png', '.jpg'),
                       use the visualizer tool instead.
            question: [Optional] A natural language question about the file. If omitted, returns the file’s text content.
            mode: Processing mode:
                  - "initial": If the file is short or you only want a brief caption.
                  - "forward": To generate a caption with three sections:
                      '1. Short answer', '2. Extremely detailed answer',
                      '3. Additional Context on the document and question asked'.

        Returns:
            A string with either the raw text content of the file or the LLM‑generated answer.
        """
        result = md_converter.convert(file_path)

        # Disallow image files.
        if file_path.lower().endswith((".png", ".jpg")):
            raise Exception("Cannot use inspect_file_as_text tool with images: use visualizer instead!")

        # For zip files, simply return the extracted text.
        if ".zip" in file_path:
            return result.text_content

        # If no question is provided, return the file content.
        if not question:
            return result.text_content

        if mode == "initial":
            if len(result.text_content) < 4000:
                return "Document content: " + result.text_content
            messages = [
                {
                    "role": "system",
                    "content": "Here is a file:\n### " + str(result.title) + "\n\n" + result.text_content[:text_limit],
                },
                {
                    "role": "user",
                    "content": (
                        "Now please write a short, 5 sentence caption for this document that could help someone "
                        "asking this question: " + question + "\n\nDon't answer the question yourself! Just provide useful notes on the document."
                    ),
                },
            ]
        else:
            messages = [
                {
                    "role": "system",
                    "content": "You will have to write a short caption for this file, then answer this question:" + question,
                },
                {
                    "role": "user",
                    "content": "Here is the complete file:\n### " + str(result.title) + "\n\n" + result.text_content[:text_limit],
                },
                {
                    "role": "user",
                    "content": (
                        "Now answer the question below. Use these three headings: '1. Short answer', '2. Extremely detailed answer', "
                        "'3. Additional Context on the document and question asked'" + question
                    ),
                },
            ]
        # Call the model with the constructed messages.
        response = await model.run(messages) if hasattr(model, "run") else model(messages)
        return response.content

    return inspect_file_as_text
