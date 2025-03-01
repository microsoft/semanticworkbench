# Content Safety for Semantic Workbench

This library provides content safety evaluators to screen and filter potentially harmful content in Semantic Workbench assistants. It helps ensure that user-generated, model-generated, and assistant-generated content is appropriate and safe.

## Key Features

- **Multiple Providers**: Support for both Azure Content Safety and OpenAI Moderations API
- **Unified Interface**: Common API regardless of the underlying provider
- **Configuration UI**: Integration with Semantic Workbench's configuration system
- **Flexible Integration**: Easy to integrate with any assistant implementation

## Available Evaluators

### Combined Content Safety Evaluator

The `CombinedContentSafetyEvaluator` provides a unified interface for using various content safety services:

```python
from content_safety.evaluators import CombinedContentSafetyEvaluator, CombinedContentSafetyEvaluatorConfig
from content_safety.evaluators.azure_content_safety.config import AzureContentSafetyEvaluatorConfig

# Configure with Azure Content Safety
config = CombinedContentSafetyEvaluatorConfig(
    service_config=AzureContentSafetyEvaluatorConfig(
        endpoint="https://your-resource.cognitiveservices.azure.com/",
        api_key="your-api-key",
        threshold=0.5,  # Flag content with harm probability above 50%
    )
)

# Create evaluator
evaluator = CombinedContentSafetyEvaluator(config)

# Evaluate content
result = await evaluator.evaluate("Some content to evaluate")
```

### Azure Content Safety Evaluator

Evaluates content using Azure's Content Safety service:

```python
from content_safety.evaluators.azure_content_safety import AzureContentSafetyEvaluator, AzureContentSafetyEvaluatorConfig

config = AzureContentSafetyEvaluatorConfig(
    endpoint="https://your-resource.cognitiveservices.azure.com/",
    api_key="your-api-key",
    threshold=0.5
)

evaluator = AzureContentSafetyEvaluator(config)
result = await evaluator.evaluate("Content to check")
```

### OpenAI Moderations Evaluator

Evaluates content using OpenAI's Moderations API:

```python
from content_safety.evaluators.openai_moderations import OpenAIContentSafetyEvaluator, OpenAIContentSafetyEvaluatorConfig

config = OpenAIContentSafetyEvaluatorConfig(
    api_key="your-openai-api-key",
    threshold=0.8,  # Higher threshold (80%)
    max_item_size=4000  # Automatic chunking for longer content
)

evaluator = OpenAIContentSafetyEvaluator(config)
result = await evaluator.evaluate("Content to check")
```

## Integration with Assistants

To integrate with a Semantic Workbench assistant:

```python
from content_safety.evaluators import CombinedContentSafetyEvaluator
from semantic_workbench_assistant.assistant_app import ContentSafety

# Define evaluator factory
async def content_evaluator_factory(context):
    config = await assistant_config.get(context.assistant)
    return CombinedContentSafetyEvaluator(config.content_safety_config)

# Create content safety component
content_safety = ContentSafety(content_evaluator_factory)

# Add to assistant
assistant = AssistantApp(
    assistant_service_id="your-assistant",
    assistant_service_name="Your Assistant",
    content_interceptor=content_safety
)
```

## Configuration UI

The library includes Pydantic models with UI annotations for easy integration with Semantic Workbench's configuration interface. These models generate appropriate form controls in the assistant configuration UI.

## Evaluation Results

Evaluation results include:
- Whether content was flagged as unsafe
- Detailed categorization (violence, sexual, hate speech, etc.)
- Confidence scores for different harm categories
- Original response from the provider for debugging

## Learn More

See the [Responsible AI FAQ](../../../RESPONSIBLE_AI_FAQ.md) for more information about content safety in the Semantic Workbench ecosystem.