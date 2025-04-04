Bugs to fix:

- ✅ Let's change the intial command from /start-coordinator to just /start.
- ✅ Let's not mention any other commands when starting a conversation (e.g. /add-goal or /add-kb-section). Instead, just describe what the coordinator (or team member) should do/say to get started.
- ✅ In coordinator mode, let's put the project-id at the top of the inspector panel just like it is in team mode.
- I'm getting this error on project assistant startup in the terminal:
  ```
  /home/payne/repos/semanticworkbench/assistants/project-assistant/.venv/lib/python3.11/site-packages/pydantic/main.py:426: UserWarning: Pydantic serializer warnings:
  PydanticSerializationUnexpectedValue: Expected `<class 'pydantic.networks.HttpUrl'>` but got `<class 'str'>` with value `'https://semantic-wb-openai-eastus-02.openai.azure.com/'` - serialized value may not be as expected.
  PydanticSerializationUnexpectedValue: Expected `OpenAIServiceConfig` but got `AzureOpenAIServiceConfig` with value `AzureOpenAIServiceConfig(...nai_deployment='gpt-4o')` - serialized value may not be as expected
  PydanticSerializationUnexpectedValue(Expected `<class 'pydantic.networks.HttpUrl'>` but got `<class 'str'>` with value `'https://semantic-wb-openai-eastus-02.openai.azure.com/'` - serialized value may not be as expected.)
  PydanticSerializationUnexpectedValue: Expected `<class 'pydantic.networks.HttpUrl'>` but got `<class 'str'>` with value `'https://lightspeed-content-safety.cognitiveservices.azure.com/'` - serialized value may not be as expected.
  PydanticSerializationUnexpectedValue: Expected `OpenAIContentSafetyEvaluatorConfig` but got `AzureContentSafetyEvaluatorConfig` with value `AzureContentSafetyEvaluat...iveservices.azure.com/')` - serialized value may not be as expected
  PydanticSerializationUnexpectedValue(Expected `<class 'pydantic.networks.HttpUrl'>` but got `<class 'str'>` with value `'https://lightspeed-content-safety.cognitiveservices.azure.com/'` - serialized value may not be as expected.)
  return self.__pydantic_serializer__.to_python(
  ```
- When in one conversation, updates are no longer triggering updates in the other conversation (either coordinator to team or team to coordinator).
