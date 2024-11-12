# Chat Driver

This is a wrapper around the OpenAI Chat Completion library that gives you a
"ChatGPT"-like interface.

You can register functions to be used as either _commands_ (allowing the user to
issue them with a `/<cmd>` message) or _tool functions_ (allowing the assistant
to optionally call them as it generates a response) or both.

Chat history is maintained for you in-memory. We also provide a local message
provider that will store chat history in a file, or you can implement your own
message provider.

All interactions with the OpenAI are saved as "metadata" on the request allowing
you to do whatever you'd like with it. It is logged for you.

For users of the Semantic Workbench, an additional module is provided to make it
simple to create an AsyncClient from Workbench-type config.

See [this notebook](../skills/notebooks/notebooks/chat_driver.ipynb) for
usage examples.
