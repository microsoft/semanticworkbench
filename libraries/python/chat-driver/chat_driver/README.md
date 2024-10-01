# Chat Driver

This is a wrapper around the OpenAI Chat Completion library that gives you a
"ChatGPT"-like interface.

You can register functions to be used as either _commands_ (allowing the user to
issue them with a `/<cmd>` message) or _tool functions_ (allowing the assistant
to optionally call them as it generates a response) or both.

Session state and chat history are maintained for you.

All interactions with the OpenAI service can be logged.

For users of the Semantic Workbench, an additional module is provided to make it
simple to create an AsyncClient from Workbench-type config.

See [this notebook](../../../skills/notebooks/notebooks/chat_driver.ipynb) for
usage examples.

## Future Work

- This chat driver does not yet support json_schema nicely. The
  ChatCompletionAPI recently added a TypeChat-like capability to ensure the
  responses are valid JSON of the type specified in the request. Adding that
  here would make a lot of sense.
- This chat driver does not yet support OpenAI-like "File search" or Claude-like
  "artifacts". Adding something like that here would make a lot of sense.
