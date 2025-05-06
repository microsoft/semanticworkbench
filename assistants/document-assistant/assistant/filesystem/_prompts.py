from openai.types.chat import (
    ChatCompletionToolParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition

FILES_PROMPT = """## Filesystem
You have available a filesystem that you can interact with via tools. \
You can read all files using the `view` tool. This is for you to understand what to do next. The user can also see these so no need to repeat them.
Certain file types are editable only via the `edit_file` tool.
Files are marked as editable using Linux file permission bits, which are denoted inside the parathesis after the filename. \
A file with permission bits `-rw-` is editable, view-only files are marked with `-r--`. \
The editable Markdown files are the ones that are shown side-by-side. \
You do not have to repeat their file contents in your response as the user can see them.
Files that are read-only are known as "attachments" and have been appended to user's message when they uploaded them."""

VIEW_TOOL = {
    "type": "function",
    "function": {
        "name": "view",
        "description": "Reads the content of a file specified by the path.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "The relative path to the file.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
    },
}

VIEW_TOOL_OBJ = ChatCompletionToolParam(
    function=FunctionDefinition(
        name=VIEW_TOOL["function"]["name"],
        description=VIEW_TOOL["function"]["description"],
        parameters=VIEW_TOOL["function"]["parameters"],
        strict=True,
    ),
    type="function",
)
