# Azure Content Safety Evaluator for Semantic Workbench Assistants

This is a Content Safety Evaluator for use with the Content Safety component of the Semantic Workbench. This evaluator is designed to be used with the Azure Content Safety service for evaluating the safety of content.

See more info at: [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety)

## Responsible AI

Use this evaluator to ensure that the content being processed by your assistant and being displayed to users is safe and appropriate. This is especially important when dealing with user-generated or model-generated content, but can also be useful for code-generated content as well.

See the [Responsible AI FAQ](../../../RESPONSIBLE_AI_FAQ.md) for more information.

## Pre-requisites

- Create an Azure account and add an `Azure AI Content Safety` resource.
  - [Create an Azure account](https://azure.microsoft.com/free/)
  - [Add an Azure AI Content Safety resource](https://portal.azure.com/#create/Microsoft.CognitiveServicesContentSafety)
  - This code has been tested on the `S0` pricing tier - if you verify it works on the free tier, please let us know.
- Get the `Endpoint` and `Key` from the Azure portal by navigating to the `Resource Management` > `Keys and Endpoint` section of the resource.

## Usage

- Add the evaluator package to your python assistant project's `pyproject.toml` file.
  - Find the `[tool.poetry.dependencies]` section
  - Add the following line:
    ```toml
    azure-content-safety-evaluator = { path = "path/to/libraries/content-safety/azure-content-safety-evaluator" }
    ```
  - If you are using the recommended path structure (`/<your_projects>/<your_assistant_name>`), the path will be:
    ```toml
    azure-content-safety-evaluator = { path = "../../libraries/content-safety/azure-content-safety-evaluator" }
    ```
