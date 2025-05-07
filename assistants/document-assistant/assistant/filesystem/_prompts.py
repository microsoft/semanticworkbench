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

EDIT_TOOL_DESCRIPTION_HOSTED = """Edits the Markdown file at the provided path, focused on the given task.
The user has Markdown editor available that is side by side with this chat.
Remember that the editable files are the ones that have the `-rw-` permission bits. \
If you provide a new file path, it will be created for you and then the editor will start to edit it (from scratch). \
Name the file with capital letters and spacing like "Weekly AI Report.md" or "Email to Boss.md" since it will be directly shown to the user in that way.
Provide a task that you want it to do in the document. For example, if you want to have it expand on one section, \
you can say "expand on the section about <topic x>". The task should be at most a few sentences. \
Do not provide it any additional context outside of the task parameter. It will automatically be fetched as needed by this tool.

Args:
    path: The relative path to the file.
    task: The specific task that you want the document editor to do."""

EDIT_TOOL_DESCRIPTION_LOCAL = """The user has a file editor corresponding to the file type, open like VSCode, Word, PowerPoint, TeXworks (+ MiKTeX), open side by side with this chat.
Use this tool to create new files or edit existing ones.
If you provide a new file path, it will be created for you and then the editor will start to edit it (from scratch).
Name the file with capital letters and spacing like "Weekly AI Report.md" or "Email to Boss.md" since it will be directly shown to the user in that way.
Provide a task that you want it to do in the document. For example, if you want to have it expand on one section,
you can say "expand on the section about <topic x>". The task should be at most a few sentences.
Do not provide it any additional context outside of the task parameter. It will automatically be fetched as needed by this tool.

Args:
    path: The relative path to the file.
    task: The specific task that you want the document editor to do."""
