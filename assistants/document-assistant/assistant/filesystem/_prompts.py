# Copyright (c) Microsoft. All rights reserved.

from openai.types.chat import (
    ChatCompletionToolParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition

FILES_PROMPT = """## Context Management

The following describes the actions you must take to make sure that you always have the most relevant context to help the user with their current task or question.
You have available a filesystem that you can interact with via tools \
to retrieve files that a user may have created, attached, or are parts of previous conversations. \
You can read any file using the `view` tool which is critical to gathering the necessary context to complete the user's request.
Certain file types are editable, but *only* via the `edit_file` tool. \
Files are marked as editable using Linux file permission bits. \
A file with permission bits `-rw-` is editable, view-only files are marked with `-r--`. \
Editable Markdown files are the ones that are shown side-by-side in the app. \
Do not repeat their file contents in your response as the user can already see the rendered Markdown. \
Instead, summarize the changes made to the file in your response if the `edit_file` tool was used.
Files that are read-only are known as "attachments" and are initially appended to user's message at the time they uploaded them. \
Eventually they might fall out of your context window and you will need to use the `view` tool to read them again if you need it. \
A summary of the file content has been provided to you to better understand what the file is about.
There are more files that you can access. First call the `ls` tool to list all files available in the filesystem.

### Recent & Relevant Files

You can read the following files in again using the `view` tool if they are needed. \
If they are editable you can also use the `edit_file` tool to edit them.
Paths are mounted at different locations depending on the type of file and you must always use the absolute path to the file, starting with `/` for any path.
- Editable files are mounted at `/editable_documents/editable_file.md`.
- User uploaded files or "attachments" are mounted at `/attachments/attachment.pdf`."""


ARCHIVES_ADDON_PROMPT = """### Conversation Memories and Archives

You have a limited context window, which means that some of the earlier parts of the conversation may fall out of your context.
To help you with that, below you will find summaries of older parts of the conversation that have been "archived". \
You should use these summaries as "memories" to help you understand the historical context and preferences of the user. \
Note that some of these archived conversation may still be visible to you in the conversation history.
If the current user's task requires you to access the full content of the conversation, you can use the `view` tool to read the archived conversations. \
Historical conversations are mounted at `/archives/conversation_1234567890.json`"""

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
                    "description": "The absolute path to the file. Must start with `/` followed by the mount point, e.g. `/editable_documents/filename.md`.",
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

LS_TOOL = {
    "type": "function",
    "function": {
        "name": "ls",
        "description": "Lists all other available files.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
}

LS_TOOL_OBJ = ChatCompletionToolParam(
    function=FunctionDefinition(
        name=LS_TOOL["function"]["name"],
        description=LS_TOOL["function"]["description"],
        parameters=LS_TOOL["function"]["parameters"],
    ),
    type="function",
)

EDIT_TOOL_DESCRIPTION_HOSTED = """Edits the Markdown file at the provided path, focused on the given task.
The user has Markdown editor available that is side by side with this chat.
Remember that the editable files are the ones that have the `-rw-` permission bits. \
They also must be mounted at `/editable_documents/` and have a `.md` extension. \
If you provide a new file path, it will be created for you and then the editor will start to edit it (from scratch). \
Name the file with capital letters and spacing like "/editable_documents/Weekly AI Report.md" or "/editable_documents/Email to Boss.md" since it will be directly shown to the user in that way.
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


FILE_SUMMARY_SYSTEM = """You will be provided the content of a file. \
It is your goal to factually, accurately, and concisely summarize the content of the file.
You must do so in less than 3 sentences or 100 words."""
