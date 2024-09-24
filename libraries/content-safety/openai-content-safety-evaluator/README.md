# OpenAI Content Safety Evaluator for Semantic Workbench Assistants

This is a Content Safety Evaluator for use with the Content Safety component of the Semantic Workbench. This evaluator is designed to be used with the OpenAI moderation endpoint for evaluating the safety of content.

See more info at: [Moderation - OpenAI Platform](https://platform.openai.com/docs/guides/moderation/overview)

## Responsible AI

Use this evaluator to ensure that the content being processed by your assistant and being displayed to users is safe and appropriate. This is especially important when dealing with user-generated or model-generated content, but can also be useful for code-generated content as well.

See the [Responsible AI FAQ](../../../RESPONSIBLE_AI_FAQ.md) for more information.

## Usage

- Add the evaluator package to your python assistant project's `pyproject.toml` file.
  - Find the `[tool.poetry.dependencies]` section
  - Add the following line:
    ```toml
    openai-content-safety-evaluator = { path = "path/to/libraries/content-safety/openai-content-safety-evaluator" }
    ```
  - If you are using the recommended path structure (`/<your_projects>/<your_assistant_name>`), the path will be:
    ```toml
    openai-content-safety-evaluator = { path = "../../libraries/content-safety/openai-content-safety-evaluator" }
    ```
