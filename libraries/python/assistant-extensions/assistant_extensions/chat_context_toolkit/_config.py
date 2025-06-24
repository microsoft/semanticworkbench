from typing import Annotated

from pydantic import BaseModel, Field


class ChatContextConfigModel(BaseModel):
    """
    Configuration model for chat context toolkit settings. This model is provided as a convenience for assistants
    that want to use the chat context toolkit features, and provide configuration for users to edit.
    Assistants can leverage this model by adding a field of this type to their configuration model.

    ex:
    ```python
    class MyAssistantConfig(BaseModel):
        chat_context: ChatContextConfigModel = ChatContextConfigModel()
    ```
    """

    high_priority_token_count: Annotated[
        int,
        Field(
            title="High Priority Token Count",
            description="The number of tokens to consider high priority when abbreviating message history.",
        ),
    ] = 30_000

    archive_token_threshold: Annotated[
        int,
        Field(
            title="Token threshold for conversation archiving",
            description="The number of tokens to include in archive chunks when archiving the conversation history.",
        ),
    ] = 20_000
