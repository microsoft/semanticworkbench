# Message Metadata

Each message, of any message type, can contain a `metadata` property. This property is a dictionary that can contain any information that the sender wants to include. The contents of this property are not interpreted by the service, but can be accessed by all that have access to the message.

The app has built-in support for a few metadata child properties, which can be used to control the behavior of the app. These properties are:

-   `attribution`: A string that will be displayed after the sender of the message. The intent is to allow the sender to indicate the source of the message, possibly coming from an internal part of its system.

-   `debug`: A dictionary that can contain additional information that can be used for debugging purposes. If included, it will cause the app to display a button that will allow the user to see the contents of the dictionary in a popup for further inspection.

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
        }
    }
}
```

Additional metadata child properties can be added by the user, and the app will ignore them, but they will be available to other systems that have access to the message.
