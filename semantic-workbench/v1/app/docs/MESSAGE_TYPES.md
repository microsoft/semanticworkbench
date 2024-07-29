# Message Types

There are a few different types of messages that can be sent to a conversation within the app. Each message type is rendered differently, and the intent is that each is used for a different purpose. Assistants should consider the message type that best fits the content they are sending and should also consider the message type when interpreting messages received.

## Chat

The `chat` message type is the most common message type. It is used for sending back and forth communication with the other participants of a conversation. The app will render the message as a chat bubble, with the text displayed in the bubble. The sender of the message will be displayed at the top of the bubble, and the message will be displayed below the sender. The app will also display the time the message was sent.

Assistants should use the `chat` message type for sending responses to the user, asking questions, or any other communication that is intended to be displayed in the chat interface as part of the conversation. Generally, `chat` messages should be considered as part of the chat history whenever performing options that consider the history of the conversation. Assistants should not use the `chat` message type for sending messages that are not intended to be part of the conversation, such as system messages, status updates (like "thinking..." or "typing...") or messages that are not intended to be displayed in the chat interface.

## Log

The `log` message type is used for sending messages that are not intended to be displayed in the chat interface. The app will not render the message in the chat interface, but the message will be logged in the conversation history and can be accessed by assistants and the system itself.

Assistants should use the `log` message type for sending debug information or any other communication that is not intended to be displayed in the chat interface. Generally, `log` messages should not be considered as part of the chat history whenever performing options that consider the history of the conversation. Assistants could consider reading the log messages when debugging or building features that leverage this information.

## Note

The `note` message type is used for sending messages that are intended to be displayed in the chat interface but are not part of the conversation. The app will render the message differently than a `chat` message. The sender of the message will be displayed at the top of the message, and the message will be displayed below the sender. The app will also display the time the message was sent.

Assistants should use the `note` message type for sending content to accompany the conversation or show additional information that is not part of the conversation (like steps it took behind the scene, code it generated, etc.). Generally, `note` messages should not be considered as part of the chat history whenever performing options that consider the history of the conversation.

## Notice

The `notice` message type is used for sending short, one-line update messages that are intended to be displayed in the chat interface. The app will render the message differently than a `chat` message. The message will be displayed in a small, single-line display, and the sender of the message will not be displayed. These are intended to be used for system-like messages that should also persist in the conversation history.

Assistants should use the `notice` message type for sending short, one-line update messages that are intended to be displayed in the chat interface. Generally, `notice` messages should be considered as part of the chat history whenever performing options that consider the history of the conversation. They should not include a "typing..." message in this category, but they might include a "<assistant> changed its operation mode to <x>" kind of message.

## Command / Command Response

The `command` and `command_response` message types are used for sending commands to the assistant and receiving responses from the assistant. The app will render the message differently than a `chat` message and can be optionally considered or not as part of the chat history whenever performing options that consider the history of the conversation.

Any `chat` messages that start with a `/` will be automatically converted to a `command` message in the user interface and assistants _should_ do the same.

Optionally, `directed_at` metadata may be populated via the input UX or by the assistant that generates the command. The `directed_at` metadata is used to specify the target of the command. It is up to the assistant to interpret the `directed_at` metadata and decide how to handle the command. For example, you code your assistant to only respond to commands that are directed at it. Note that all commands are sent to all assistants in the conversation and each can choose to respond or ignore the command, regardless of the `directed_at` metadata.

Assistants should respond to `command` messages with a `command_response` message. The `command_response` message should contain the response to the command. The app will render the `command_response` message differently than a `chat` message and is also optionally considered or not as part of the chat history whenever performing options that consider the history of the conversation.
