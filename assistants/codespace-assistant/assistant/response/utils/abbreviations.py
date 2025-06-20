from message_history_manager.history.tool_abbreviations import Abbreviations, ToolAbbreviations

tool_abbreviations = ToolAbbreviations({
    "read_file": Abbreviations(
        tool_message_replacement="The content that was read from the file has been removed due to token limits. Please use read_file to retrieve the most recent content."
    ),
    "write_file": Abbreviations(
        tool_message_replacement="The content that was written to the file has been removed due to token limits. Please use read_file to retrieve the most recent content if you need it."
    ),
    "list_directory": Abbreviations(
        tool_message_replacement="The list of files and directories has been removed due to token limits. Please call the tool to retrieve the list again if you need it."
    ),
    "create_directory": Abbreviations(
        tool_message_replacement="The result of this tool call the file has been removed due to token limits. Please use list_directory to retrieve the most recent list if you need it."
    ),
    "edit_file": Abbreviations(
        tool_call_argument_replacements={
            "edits": [
                {
                    "oldText": "The oldText has been removed from this tool call due to reaching token limits. Please use read_file to retrieve the most recent content.",
                    "newText": "The newText has been removed from this tool call due to reaching token limits. Please use read_file to retrieve the most recent content.",
                }
            ]
        },
        tool_message_replacement="The result of this tool call the file has been removed due to token limits. Please use read_file to retrieve the most recent content if you need it.",
    ),
    "search_files": Abbreviations(
        tool_message_replacement="The search results have been removed due to token limits. Please call the tool to search again if you need it."
    ),
    "get_file_info": Abbreviations(
        tool_message_replacement="The results have been removed due to token limits. Please call the tool to again if you need it."
    ),
    "read_multiple_files": Abbreviations(
        tool_message_replacement="The contents of these files have been removed due to token limits. Please use the tool again to read the most recent contents if you need them."
    ),
    "move_file": Abbreviations(
        tool_message_replacement="The result of this tool call the file has been removed due to token limits. Please use list_directory to retrieve the most recent list if you need it."
    ),
    "list_allowed_directories": Abbreviations(
        tool_message_replacement="The result of this tool call the file has been removed due to token limits. Please call this tool again to retrieve the most recent list if you need it."
    ),
})
