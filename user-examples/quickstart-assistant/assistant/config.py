from openai_assistant import openai_chat


class AssistantConfigModel(openai_chat.OpenAIChatConfigModel):
    # add any additional configuration fields
    pass


assistant_config_ui_schema = {
    **openai_chat.openai_chat_config_ui_schema,
    # add UI schema for the additional configuration fields
}
