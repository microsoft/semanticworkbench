# Copyright (c) Microsoft. All rights reserved.

from openai.types.chat import (
    ChatCompletionToolParam,
)
from openai.types.shared_params.function_definition import FunctionDefinition

USER_GUIDANCE_INSTRUCTIONS = """You can generate dynamic UI elements using the `dynamic_ui_preferences` tool to present \
the user choices to better understand their needs and preferences. \
They can also be used to better understand the user's preferences on how to use the other tools and capabilities; for example preferences for writing.
The generated UI elements will be displayed on the side of the chat in a side panel.
Let the user know they can make choices in that UI and click "Save Preferences" which will then be used for future interactions.
At the beginning of conversations where the user is ambiguous or just getting started, always call `dynamic_ui_preferences` to generate UI elements. \
In future turns, you must still call the tool when the user is ambiguous or working on a new task.
Be aware that there is a background process that will be also generating additional UI elements, but do not let this impact how often you choose to call the tool.
- Generate at most 4 dynamic UI elements per message. \
Generating no elements is completely acceptable. Return an empty array if you do not want to generate any.
- Do not generate new elements for information that the user has already provided.
- If the previous dynamic UI elements cover the aspects of the conversation, do not generate any new elements. \
Pay attention to the latest user message as the key signal for which elements to generate. \
If the user is providing context or information, likely there is no or little need for new elements. \
For example, if you are on the same topic or task, it is not necessary to generate new elements. \
If the user is asking questions or needs help, and existing elements do not cover it, this is a good time to generate new elements.
- Place the most important ones first, as those will be shown first.
- Use checkboxes when you want to give them the ability to choose multiple options. \
You should try to limit the number of options to under 8 (less is better) for checkboxes to avoid overwhelming the user.
- Use dropdowns when you have a list of options you want to enforce only a single selection.
- Make sure the options, where appropriate, give the user a chance to convey something like "other", \
or are comprehensive such as including "less than"/"greater than" (like for prices) to avoid selections where none of the users apply to them. \
Do not include options like "none" as the user can always select nothing. \
Keep choices short (1-2 words) and easy to understand for the user, given what you think their level of expertise is.
- Textboxes should be used only when necessary. Such as when it would result in too many choices (10+) or you need details.
- When generating the title, make sure the title can be understood even out of context \
since there might be a lot of UI elements generated over time and we want to make sure the user can understand what it is referring to.

### Current Dynamic UI State
- The current UI schema is after the "ui_elements" key in the JSON object.
- The current selections (if any) are in the "form_data" key in the JSON object. \
Note that textboxes are indexed by their order in the list of UI elements, so the first textbox if it has data will be "textbox_0", the second "textbox_1", etc.
- Any current choices the user has made will be reflected in the conversation as separate messages prefixed with 'User updated UI:' and then the change they made.
- Under no circumstances should you generate the same or very similar choices. You can always generate an empty array.
These are the current dynamic UI elements that have been generated:"""

DYNAMIC_UI_TOOL_RESULT = """"The newly generated dynamic UI components are being displayed to the user. \
Let them know they can interact with them in the 'Dynamic User Preferences' tab of the assistant canvas. \
Once they have made their selections, they can click 'Save Preferences' to have them be used by you once they send another message."""

DYNAMIC_UI_TOOL_NAME = "dynamic_ui_preferences"
DYNAMIC_UI_TOOL = {
    "type": "function",
    "function": {
        "name": DYNAMIC_UI_TOOL_NAME,
        "description": "Generate dynamic UI elements to present to a user choices to better understand their needs and preferences. Generate an empty array if no elements are currently appropriate.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "ui_elements": {
                    "type": "array",
                    "description": "A list of dynamic UI elements to be shown to the user.",
                    "items": {
                        "anyOf": [
                            {
                                "type": "object",
                                "properties": {
                                    "checkboxes": {
                                        "type": "object",
                                        "description": "A list of checkboxes to be shown to the user.",
                                        "properties": {
                                            "title": {
                                                "type": "string",
                                                "description": "The label of the component.",
                                            },
                                            "options": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "value": {
                                                            "type": "string",
                                                            "description": "The value of the checkbox option.",
                                                        },
                                                    },
                                                    "required": ["value"],
                                                    "additionalProperties": False,
                                                },
                                            },
                                        },
                                        "required": ["title", "options"],
                                        "additionalProperties": False,
                                    }
                                },
                                "required": ["checkboxes"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "dropdown": {
                                        "type": "object",
                                        "description": "A dropdown to be shown to the user.",
                                        "properties": {
                                            "title": {
                                                "type": "string",
                                                "description": "The label of the component.",
                                            },
                                            "options": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "value": {
                                                            "type": "string",
                                                            "description": "The value of the dropdown option.",
                                                        },
                                                    },
                                                    "required": ["value"],
                                                    "additionalProperties": False,
                                                },
                                            },
                                        },
                                        "required": ["title", "options"],
                                        "additionalProperties": False,
                                    }
                                },
                                "required": ["dropdown"],
                                "additionalProperties": False,
                            },
                            {
                                "type": "object",
                                "properties": {
                                    "textbox": {
                                        "type": "string",
                                        "description": "A textbox will be created with the value provided.",
                                    }
                                },
                                "required": ["textbox"],
                                "additionalProperties": False,
                            },
                        ]
                    },
                }
            },
            "required": ["ui_elements"],
            "additionalProperties": False,
        },
    },
}

DYNAMIC_UI_TOOL_OBJ = ChatCompletionToolParam(
    function=FunctionDefinition(
        name=DYNAMIC_UI_TOOL_NAME,
        description=DYNAMIC_UI_TOOL["function"]["description"],
        parameters=DYNAMIC_UI_TOOL["function"]["parameters"],
        strict=True,
    ),
    type="function",
)
