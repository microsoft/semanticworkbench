# Semantic Workbench's Responsible AI FAQ

## What is Semantic Workbench?

- Semantic Workbench is a web application intended to help prototyping assistants during the development phase.
- Semantic Workbench provides a user interface for creating conversations with one or more assistants, including a configuration user interface, and a service to connect custom assistants.

## What is/are Semantic Workbench’s intended use(s)?

- Semantic Workbench is designed for prototyping assistants, running conversations and testing assistants behavior.

## How was Semantic Workbench evaluated? What metrics are used to measure performance?

Semantic Workbench has been built from the ground up specifically for the experimentation use-case. Other user interfaces and tools have been evaluated, but none allowed to prototype assistants decoupled from a specific underlying technology stack such as AI models or frameworks.

Semantic Workbench does not mandate any specific technology or framework. 

Developers can use any of preferred technology and connect their bots to Semantic Workbench to benefit from its user interface, including configuration, debugging and visualization tools.

## What are the limitations of Semantic Workbench? How can users minimize the impact of Semantic Workbench’s limitations when using the system?

- Semantic Workbench is not an assistant in itself, it only allows to connect and test existing assistants.

- Intelligent assistants must be developed with usual IDEs and development tools like Semantic Kernel, Langchain, Autogen, following the best practices there recommended, for instance [Responsible AI and Semantic Kernel](https://learn.microsoft.com/semantic-kernel/when-to-use-ai/responsible-ai) and [LangSmith](https://www.langchain.com/langsmith).

- The workbench is unable to automatically discover agents: once the code for an agent is ready, some extra code needs to be added in order to connect the assistant to Semantic Workbench.

- Developers connecting their agents to Semantic Workbench are responsible for implementing security and safety into their agents, using, for example, [Azure AI Content Safety](https://azure.microsoft.com/eproducts/ai-services/ai-content-safety) and [Microsoft Purview](https://www.microsoft.com/security/business/microsoft-purview), and leveraging tools like [Responsible AI Toolbox](https://github.com/microsoft/responsible-ai-toolbox).

- When using Semantic Workbench to test an assistant, developers should carefully observe the bot’s behavior and use the debugging tools to investigate any unexpected outcomes. Although Semantic Workbench does not automatically detect harmful, inaccurate, or biased content, it enables developers to run and debug conversations, which helps identify and fix issues, improve the bot’s behavior, and edit prompts and code as necessary.

- Developers using Semantic Workbench can adopt a user-centric approach in designing applications, ensuring that users are well-informed and have the ability to approve any actions taken by the AI. Semantic Workbench exposes all the information provided by the connected assistants, so it's important that developers code these assistants to expose their rationale, prompts, and state.

- Additionally, intelligent assistants developers should implement mechanisms to monitor and filter any automatically generated information, if deemed necessary.

- By addressing responsible AI issues in this manner, developers can create assistants that are not only efficient and useful but also adhere to ethical guidelines and prioritize user trust and safety.

## What operational factors and settings allow for effective and responsible use of Semantic Workbench?

- First and foremost, developers using Semantic Workbench can precisely define user interactions and how user data is managed in the source code of their intelligent assistants.

- If a prototype assistant runs a sequence of components, additional risks/failures may arise when using non-deterministic behavior. To mitigate this, developers can:

  - Implement safety measures and bounds on each component to prevent undesired outcomes.
  - Add output to the user to maintain control and awareness of the system's state.
  - In multi-agent scenarios, build in places that prompt the user for a response, ensuring user involvement and reducing the likelihood of undesired results due to multi-agent looping.

- When working with AI, the developer can enable content moderation in the AI platforms used, and has complete control on the prompts being used, including the ability to define responsible boundaries and guidelines. For instance:

  - When using Azure OpenAI, by default the service includes a content filtering system that works alongside core models. This system works by running both the prompt and completion through an ensemble of classification models aimed at detecting and preventing the output of harmful content. In addition to the content filtering system, the Azure OpenAI Service performs monitoring to detect content and/or behaviors that suggest use of the service in a manner that might violate applicable product terms. The filter configuration can be adjusted, for example to block also "low severity level" content. See [here](https://learn.microsoft.com/azure/ai-services/openai/concepts/content-filter) for more information.

  - The developer can integrate Azure AI Content Safety to detect harmful user-generated and AI-generated content, including text and images. The service includes an interactive Studio online tool with templates and customized workflows. See [here](https://learn.microsoft.com/azure/ai-services/content-safety) for more information.

  - When using OpenAI the developer can integrate OpenAI Moderation to identify problematic content and take action, for instance by filtering it. See [here](https://platform.openai.com/docs/guides/moderation) for more information.

  - Other AI providers provide content moderation and moderation APIs, which developers can integrate with Node Engine.
