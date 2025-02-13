Introduction
------------

PydanticAI is revolutionizing the way we build AI agents by combining the power of Pydantic’s type validation with a flexible agent framework. In this comprehensive guide, we’ll explore PydanticAI’s core features and build several working examples using different AI models.

What is PydanticAI?
-------------------

PydanticAI is a new framework developed by the team behind Pydantic, specifically designed for building AI agents. It inherits Pydantic’s strong typing and validation capabilities while adding specialized features for agent development.

### Key Features

1. **Type Safety**: Built-in integration with static type checkers (mypy, pyrite)
2. **Model Support**: Compatible with multiple AI providers:

- OpenAI
- Anthropic
- Gemini
- Ollama
- Azure OpenAI

1. **Python-Centric**: Uses standard Python control flow and best practices
2. **Real-time Monitoring**: Integration with Pydantic LogFire
3. **Dependency Injection**: Unique system for providing data and services
4. **Multi-Agent Support**: Create multiple agents with different models
5. **Streaming**: Real-time LLM output with immediate validation

Prerequisites
-------------

Before we begin, ensure you have:

1. Python 3.8 or higher installed
2. OpenAI API key (for OpenAI examples)
3. Ollama installed (for local model examples)
4. Azure OpenAI access (for Azure examples)

Installation
------------

```
<pre class="brush: plain; title: ; notranslate" title="">
pip install pydantic-ai
```

Hands-on Lab: Building AI Agents
--------------------------------

### Example 1: Hello World Agent (5 lines)

Let’s start with the simplest possible agent:

```
<pre class="brush: plain; title: ; notranslate" title="">
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
model = OpenAIModel("gpt-4")
agent = Agent(model)
result = agent.run_sync("What is the capital of the United States?")
```

Save this as `hello_world.py`. When you run it, you’ll see a LogFire warning (which we’ll address later) and the response: “The capital of the United States is Washington, DC.”

### Example 2: OpenAI Agent with Environment Variables

This example demonstrates proper API key management:

```
<pre class="brush: plain; title: ; notranslate" title="">
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
import os
load_dotenv()
model = OpenAIModel("gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
agent = Agent(model)
result = agent.run_sync("What is the capital of Mexico?")
print(result.data)
```

Create a `.env` file:

```
<pre class="brush: plain; title: ; notranslate" title="">
OPENAI_API_KEY=your_api_key_here
```

### Example 3: Local Ollama Agent

For those preferring to run models locally:

```
<pre class="brush: plain; title: ; notranslate" title="">
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from colorama import Fore
model = OllamaModel(
    "llama2:3.2.1-b",
    base_url="http://localhost:11434/v1"
)
agent = Agent(model)
result = agent.run_sync("What is the capital of the United States?")
print(Fore.RED + result.data)
```

Before running, ensure Ollama is installed and running:

```
<pre class="brush: plain; title: ; notranslate" title="">
ollama run llama2:3.2.1-b
```

### Example 4: Azure OpenAI Integration

For enterprise users leveraging Azure:

```
<pre class="brush: plain; title: ; notranslate" title="">
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = AsyncAzureOpenAI(
    api_version=os.getenv("AZURE_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY")
)
model = OpenAIModel("gpt-4", openai_client=client)
agent = Agent(model)
result = agent.run_sync("What is the capital of the United States?")
print(result.data)
```

Required `.env` entries:

```
<pre class="brush: plain; title: ; notranslate" title="">
AZURE_API_VERSION=your_api_version
AZURE_ENDPOINT=your_endpoint
AZURE_API_KEY=your_api_key
```

### Example 5: Multi-Model Agent System

This advanced example shows how to chain multiple agents:

```
<pre class="brush: plain; title: ; notranslate" title="">
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.ollama import OllamaModel
from dotenv import load_dotenv
import os
load_dotenv()
# OpenAI Agent
openai_model = OpenAIModel("gpt-4", api_key=os.getenv("OPENAI_API_KEY"))
openai_agent = Agent(openai_model)
result1 = openai_agent.run_sync("What is the capital of Mexico?")
print(f"OpenAI Agent: {result1.data}")
# Get last message for context
last_message = result1.new_messages[-1]
# Ollama Agent
ollama_model = OllamaModel(
    "llama2:3.2.1-b",
    base_url="http://localhost:11434/v1"
)
ollama_agent = Agent(ollama_model)
result2 = ollama_agent.run_sync(
    "Tell me about the history of this city",
    message_history=[last_message]
)
print(f"Ollama Agent: {result2.data}")
```

Key Concepts
------------

### Agent Architecture

In PydanticAI, an agent consists of:

1. A core Agent class
2. An associated Model (OpenAI, Ollama, etc.)
3. Optional tools and system prompts
4. Runtime dependencies

### Message History

Agents maintain message history, allowing for:

- Context preservation
- Inter-agent communication
- Response validation

### Dependency Injection

PydanticAI’s dependency injection system enables:

- Runtime context updates
- Tool integration
- Testing and validation
- Service provision

### Type Safety

The framework enforces type safety through:

- Pydantic models
- Static type checking
- Runtime validation
- Structured outputs

Best Practices
--------------

1. **API Key Management**:

- Always use environment variables
- Consider using different keys for different environments

1. **Model Selection**:

- Use appropriate models for tasks
- Consider cost vs. performance
- Test with smaller models first

1. **Error Handling**:

- Implement proper try-except blocks
- Handle API rate limits
- Monitor model responses

1. **Testing**:

- Unit test individual agents
- Integration test agent chains
- Mock expensive API calls

Summary
-------

I’ll summarize the key points from the post about PydanticAI in bullet points:

- PydanticAI is a new agent framework created by the Pydantic team, specifically designed for building AI agents while leveraging Pydantic’s typing and validation capabilities.
- The framework supports multiple models including OpenAI, Anthropic, Gemini, Ollama, and Azure OpenAI, with a simple interface to implement support for additional models.
- One of its key features is type safety, making type checking as straightforward as possible through integration with static type checkers like mypy and pyrite.
- PydanticAI uses plain Python for controlling agent data flow, eliminating the need for domain-specific code or extra classes while allowing standard Python best practices.
- The framework includes real-time debugging, performance monitoring, and tracking through integration with Pydantic LogFire.
- It offers a unique dependency injection system for providing data and services to agent systems, prompts, tools, and results validators, which is particularly useful for testing.
- Agents can be created in as little as five lines of code, making it accessible for beginners while still offering advanced features for complex implementations.
- The framework allows creation of multiple agents where each agent can operate with its own model, exchanging information through message history and dynamic runtime context.
- PydanticAI provides the ability to stream LLM outputs continuously with immediate validation, ensuring rapid and accurate results.
- The framework supports tools reflection and self-correction, and can handle dynamic runtime context injection for critical data such as customer information or offline calculation results.

Conclusion
----------

PydanticAI offers a powerful, type-safe framework for building AI agents. Its Python-centric approach, combined with strong typing and validation, makes it an excellent choice for production systems. The framework’s support for multiple models and inter-agent communication enables complex AI systems while maintaining code quality and testability.

Remember to check the official documentation at `ai.pydantic.dev` for updates and advanced features.
