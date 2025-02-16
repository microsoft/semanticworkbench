# Message Metadata

Each message, of any message type, can contain a `metadata` property. This property is a dictionary that can contain any information that the sender wants to include. The contents of this property are not interpreted by the service, but can be accessed by all that have access to the message.

The app has built-in support for a few metadata child properties, which can be used to control the behavior of the app. These properties are:

-   `attribution`: A string that will be displayed after the sender of the message. The intent is to allow the sender to indicate the source of the message, possibly coming from an internal part of its system.

-   `href`: If provided, the app will display the message as a hyperlink. The value of this property will be used as the URL of the hyperlink and use the React Router navigation system to navigate to the URL when the user clicks on the message. Will be ignored for messages of type `chat`.

-   `debug`: A dictionary that can contain additional information that can be used for debugging purposes. If included, it will cause the app to display a button that will allow the user to see the contents of the dictionary in a popup for further inspection.

-   `footer_items`: A list of strings that will be displayed in the footer of the message. The intent is to allow the sender to include additional information that is not part of the message body, but is still relevant to the message.

Example:

```json
{
    "id": "1234....",
    "sender": {
        "participant_id": "1234....",
        "participant_role": "user"
    },
    "content": "Hello World!",
    "content_type": "text/plain",
    "message_type": "chat",
    "metadata": {
        "attribution": "Internal System",
        "debug": {
            "intent_generation": {
                "request": {
                    "content": ...
                },
                "response": {
                    "content": ...
                }
            },
            "response_generation": {
                "request": {
                    "content": ...
                },
                "response": {
                    "content": ...
                }
            }
        },
        "footer_items": [
            "6.8k of 50k (13%) tokens used for request",
        ]
    }
}
```

## Tools in UX via Metadata

There is experimental support for rendering tools calls and their results in the UX via metadata. This is not yet fully implemented, but the intent is to allow assistants to send messages that include both the list of tools they are going to call and then individual messages for each tool result.

To invoke this behavior, include the following metadata properties in messages that contain `tools calls`:

-   Metadata properties:

    -   `tool_calls`: A list of tool calls that the assistant is going to make. Each tool call
        -   `id: string` - The ID of the tool call.
        -   `name: string` - The name of the tool call.
        -   `arguments: Record<string, any>` - The arguments for the tool call.

-   Include an commentary from the assistant regarding the intended use of the tool(s) in the `content` of the message.
-   Message container will be based upon the `message_type` of the message. Suggestion is to use `chat`.

Example:

```json
{
    ... ConversationMessageProps,
    "content": "I will now read the README files...",
    "metadata": {
        "tool_calls": [
            {
                "id": "tool_call_1",
                "name": "Tool 1",
                "arguments": {
                    ...
                }
            },
            {
                "id": "tool_call_2",
                "name": "Tool 2",
                "arguments": {
                    ...
                }
            }
        ]
    }
}
```

Then, for each tool result, send a message with the following metadata properties:

-   Metadata properties:

    -   `tool_calls`: Same list of tool calls as above, it will be used to retrieve the
        tool call that corresponds to the tool result.
    -   `tool_result: Record<str, any>`: A dictionary with the following property (others are ignored):

        -   `tool_call_id`: The ID of the tool result.

-   The actual results of the tool call should be the `content` of the message.
-   The `message_type` will be ignored as there is a separate renderer for tool results.

Example:

```json
{
    ... ConversationMessageProps,
    "content": {
        "README.md: ..."
    },
    "metadata": {
        "tool_calls": [
            {
                "id": "tool_call_1",
                "name": "Tool 1",
                "arguments": {
                    ...
                }
            },
            {
                "id": "tool_call_2",
                "name": "Tool 2",
                "arguments": {
                    ...
                }
            }
        ],
        "tool_result": {
            "tool_call_id": "tool_result_1",
        },
    }
}
```

---

Additional metadata child properties can be added by the user, and the app will ignore them, but they will be available to other systems that have access to the message.
