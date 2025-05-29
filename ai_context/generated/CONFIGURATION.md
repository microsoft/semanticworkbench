# *.md | *.toml | Makefile | *.json | *.yml | *.yaml

[collect-files]

**Search:** ['*.md', '*.toml', 'Makefile', '*.json', '*.yml', '*.yaml']
**Exclude:** ['.venv', 'node_modules', '*.lock', '.git', '__pycache__', '*.pyc', '*.ruff_cache', 'logs', 'output', 'workbench-app', 'workbench-service', 'assistants', 'libraries', 'mcp-servers', 'examples', 'tools']
**Include:** []
**Date:** 5/29/2025, 11:45:28 AM
**Files:** 10

=== File: CLAUDE.md ===
# Semantic Workbench Developer Guidelines

## AI Context System
**Generate comprehensive codebase context for development:**
* `make ai-context-files` - Generate AI context files for all components
* Files created in `ai_context/generated/` organized by logical boundaries:
  - **Python Libraries** (by functional group):
    - `PYTHON_LIBRARIES_CORE.md` - Core API model, assistant framework, events
    - `PYTHON_LIBRARIES_AI_CLIENTS.md` - Anthropic, OpenAI, LLM clients
    - `PYTHON_LIBRARIES_EXTENSIONS.md` - Assistant/MCP extensions, content safety
    - `PYTHON_LIBRARIES_SPECIALIZED.md` - Guided conversation, assistant drive
    - `PYTHON_LIBRARIES_SKILLS.md` - Skills library with patterns and routines
  - **Assistants** (by individual implementation):
    - `ASSISTANTS_OVERVIEW.md` - Common patterns and all assistant summaries
    - `ASSISTANT_PROJECT.md` - Project assistant (most complex)
    - `ASSISTANT_DOCUMENT.md` - Document processing assistant
    - `ASSISTANT_CODESPACE.md` - Development environment assistant
    - `ASSISTANT_NAVIGATOR.md` - Workbench navigation assistant
    - `ASSISTANT_PROSPECTOR.md` - Advanced agent with artifact creation
    - `ASSISTANTS_OTHER.md` - Explorer, guided conversation, skill assistants
  - **Platform Components**:
    - `WORKBENCH_FRONTEND.md` - React app components and UI patterns
    - `WORKBENCH_SERVICE.md` - Backend API, database, and service logic
    - `MCP_SERVERS.md` - Model Context Protocol server implementations
    - `DOTNET_LIBRARIES.md` - .NET libraries and connectors
  - **Supporting Files**:
    - `EXAMPLES.md` - Sample code and getting-started templates
    - `TOOLS.md` - Build scripts and development utilities
    - `CONFIGURATION.md` - Root-level configs and project setup
    - `ASPIRE_ORCHESTRATOR.md` - Container orchestration setup

**Using AI Context for Development:**
* **New developers**: Read `CONFIGURATION.md` + `PYTHON_LIBRARIES_CORE.md` for project overview
* **Building assistants**: 
  - Start with `ASSISTANTS_OVERVIEW.md` for common patterns
  - Use specific assistant files (e.g., `ASSISTANT_PROJECT.md`) as implementation templates
* **Working on specific assistants**: Load the relevant `ASSISTANT_*.md` file for focused context
* **Library development**: Choose appropriate `PYTHON_LIBRARIES_*.md` file by functional area
* **Frontend work**: Study component patterns in `WORKBENCH_FRONTEND.md`
* **API development**: Follow service patterns from `WORKBENCH_SERVICE.md`
* **MCP servers**: Use existing servers in `MCP_SERVERS.md` as templates
* **AI tools**: Provide relevant context files for better code generation and debugging
* **Code reviews**: Reference context files to understand cross-component impacts

## Common Commands
* Build/Install: `make install` (recursive for all subdirectories)
* Format: `make format` (runs ruff formatter)
* Lint: `make lint` (runs ruff linter)
* Type-check: `make type-check` (runs pyright)
* Test: `make test` (runs pytest)
* Single test: `uv run pytest tests/test_file.py::test_function -v`
* Frontend: `cd workbench-app && pnpm dev` (starts dev server)
* Workbench service: `cd workbench-service && python -m semantic_workbench_service.start`

## Code Style
### Python
* Indentation: 4 spaces
* Line length: 120 characters
* Imports: stdlib → third-party → local, alphabetized within groups
* Naming: `snake_case` for functions/variables, `CamelCase` for classes, `UPPER_SNAKE_CASE` for constants
* Types: Use type annotations consistently; prefer Union syntax (`str | None`) for Python 3.10+
* Documentation: Triple-quote docstrings with param/return descriptions

### C# (.NET)
* Naming: `PascalCase` for classes/methods/properties, `camelCase` for parameters/local variables, `_camelCase` for private fields
* Error handling: Use try/catch with specific exceptions, `ConfigureAwait(false)` with async
* Documentation: XML comments for public APIs
* Async: Use async/await consistently with cancellation tokens

### TypeScript/React (Frontend)
* Component files: Use PascalCase for component names and files (e.g., `MessageHeader.tsx`)
* Hooks: Prefix with 'use' (e.g., `useConversationEvents.ts`)
* CSS: Use Fluent UI styling with mergeStyle and useClasses pattern
* State management: Redux with Redux Toolkit and RTK Query
* Models: Define strong TypeScript interfaces/types

## Tools
* Python: Uses uv for environment/dependency management
* Linting/Formatting: Ruff (Python), ESLint (TypeScript)
* Type checking: Pyright (Python), TypeScript compiler
* Testing: pytest (Python), React Testing Library (Frontend)
* Frontend: React, Fluent UI v9, Fluent Copilot components
* Package management: uv (Python), pnpm (Frontend)

=== File: CODE_OF_CONDUCT.md ===
# Microsoft Open Source Code of Conduct

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).

Resources:

- [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/)
- [Microsoft Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
- Contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with questions or concerns


=== File: CONTRIBUTING.md ===
# Contributing to Semantic Workbench

You can contribute to the Semantic Workbench with issues and pull requests (PRs). Simply
filing issues for problems you encounter is a great way to contribute. Contributing
code is greatly appreciated.

## Reporting Issues

We always welcome bug reports, API proposals and overall feedback. Here are a few
tips on how you can make reporting your issue as effective as possible.

### Where to Report

New issues can be reported in our [list of issues](https://github.com/microsoft/semanticworkbench/issues).

Before filing a new issue, please search the list of issues to make sure it does
not already exist.

If you do find an existing issue for what you wanted to report, please include
your own feedback in the discussion. Do consider up-voting (👍 reaction) the original
post, as this helps us prioritize popular issues in our backlog.

### Writing a Good Bug Report

Good bug reports make it easier for maintainers to verify and root cause the
underlying problem.
The better a bug report, the faster the problem will be resolved. Ideally, a bug
report should contain the following information:

- A high-level description of the problem.
- A _minimal reproduction_, i.e. the smallest size of code/configuration required
  to reproduce the wrong behavior.
- A description of the _expected behavior_, contrasted with the _actual behavior_ observed.
- Information on the environment: OS/distribution, CPU architecture, SDK version, etc.
- Additional information, e.g. Is it a regression from previous versions? Are there
  any known workarounds?

## Contributing Changes

Project maintainers will merge accepted code changes from contributors.

### DOs and DON'Ts

DO's:

- **DO** clearly state on an issue that you are going to take on implementing it.
- **DO** follow the standard coding conventions

  - [Python](https://pypi.org/project/black/)
  - [Typescript](https://typescript-eslint.io/rules/)/[React](https://github.com/jsx-eslint/eslint-plugin-react/tree/master/docs/rules)
  - [.NET](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)

- **DO** give priority to the current style of the project or file you're changing
  if it diverges from the general guidelines.
- **DO** include tests when adding new features. When fixing bugs, start with
  adding a test that highlights how the current behavior is broken.
- **DO** keep the discussions focused. When a new or related topic comes up
  it's often better to create new issue than to side track the discussion.
- **DO** blog and tweet (or whatever) about your contributions, frequently!

DON'Ts:

- **DON'T** surprise us with big pull requests. Instead, file an issue and start
  a discussion so we can agree on a direction before you invest a large amount of time.
- **DON'T** commit code that you didn't write. If you find code that you think is a good
  fit to add to Semantic Workbench, file an issue and start a discussion before proceeding.
- **DON'T** submit PRs that alter licensing related files or headers. If you believe
  there's a problem with them, file an issue and we'll be happy to discuss it.
- **DON'T** make new features, APIs, or services without filing an issue and discussing with us first.

### Breaking Changes

Contributions must maintain API signature and behavioral compatibility. Contributions
that include breaking changes will be rejected. Please file an issue to discuss
your idea or change if you believe that a breaking change is warranted.

### Suggested Workflow

We use and recommend the following workflow:

1. Create an issue for your work.
   - You can skip this step for trivial changes.
   - Reuse an existing issue on the topic, if there is one.
   - Get agreement from the team and the community that your proposed change is
     a good one.
   - Clearly state that you are going to take on implementing it, if that's the case.
     You can request that the issue be assigned to you. Note: The issue filer and
     the implementer don't have to be the same person.
2. Create a personal fork of the repository on GitHub (if you don't already have one).
3. In your fork, create a branch off of main (`git checkout -b my_branch`).
   - Name the branch so that it clearly communicates your intentions, such as
     "issue-123" or "github_handle-issue".
4. Make and commit your changes to your branch.
5. Add new tests corresponding to your change, if applicable.
6. Run the build and tests as described in the readme for the part(s) of the Semantic Workbench your changes impact to ensure that your build is clean and all tests are passing.
7. Create a PR against the repository's **main** branch.
   - State in the description what issue or improvement your change is addressing.
   - Verify that all the Continuous Integration checks are passing.
8. Wait for feedback or approval of your changes from the code maintainers.
9. When area owners have signed off, and all checks are green, your PR will be merged.

For a detailed walkthrough of this workflow, including how to set up forks and manage your Git workflow, refer to the [Detailed Workflow Walkthrough](#detailed-workflow-walkthrough) section.

### Adding Assistants

We appreciate your interest in extending Semantic Workbench's functionality through
providing assistants in the main repo. However, we want to clarify our approach to
our GitHub repository. To maintain a clean and manageable codebase we will not be
hosting assistants directly in the Semantic Workbench GitHub repository.
Instead, we encourage contributors to host their assistants in separate
repositories under their own GitHub accounts or organization. You can then
provide a link to your assistant repository in the relevant discussions, issues,
or documentation within the Semantic Workbench repository. This approach ensures
that each assistant can be maintained independently and allows for easier tracking
of updates and issues specific to each assistant. We will only provide a few assistants for demonstrating how to build your own in this repository.

### PR - CI Process

The continuous integration (CI) system will automatically perform the required
builds and run tests (including the ones you are expected to run) for PRs. Builds
and test runs must be clean.

If the CI build fails for any reason, the PR issue will be updated with a link
that can be used to determine the cause of the failure.

### Detailed Workflow Walkthrough

This detailed guide walks you through the process of contributing to our repository via forking, cloning, and managing your Git workflow.

Start by forking the repository on GitHub. This creates a copy of the repository under your GitHub account.

Clone your forked repository to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/semanticworkbench.git
cd semanticworkbench
```

Add the original repository as an upstream remote:

```bash
git remote add upstream https://github.com/microsoft/semanticworkbench.git
```

Check your remotes to ensure you have both `origin` and `upstream`:

```bash
git remote -v
```

You should see something like this:

```
origin    https://github.com/YOUR_USERNAME/semanticworkbench.git (fetch)
origin    https://github.com/YOUR_USERNAME/semanticworkbench.git (push)
upstream  https://github.com/microsoft/semanticworkbench.git (fetch)
upstream  https://github.com/microsoft/semanticworkbench.git (push)
```

To keep your fork updated with the latest changes from upstream, configure your local `main` branch to track the upstream `main` branch:

```bash
git branch -u upstream/main main
```

Alternatively, you can edit your `.git/config` file:

```ini
[branch "main"]
    remote = upstream
    merge = refs/heads/main
```

Before starting a new feature or bug fix, ensure that your fork is up-to-date with the latest changes from upstream:

```bash
git checkout main
git pull upstream main
```

Create a new branch for your feature or bug fix:

```bash
git checkout -b feature-name
```

Make your changes in the codebase. Once you are satisfied, add and commit your changes:

```bash
git add .
git commit -m "Description of your changes"
```

Push your changes to your fork:

```bash
git push origin feature-name
```

Go to your fork on GitHub, and you should see a `Compare & pull request` button. Click it and submit your pull request (PR) against the original repository’s `main` branch.

If there are changes in the main repository after you created your branch, sync them to your branch:

```bash
git checkout main
git pull upstream main
git checkout feature-name
git rebase main
```

Once your PR is merged, you can delete your branch both locally and from GitHub.

**Locally:**

```bash
git branch -d feature-name
```

**On GitHub:**
Go to your fork and delete the branch from the `Branches` section.


=== File: KNOWN_ISSUES.md ===
# Semantic Workbench Known Issues

You may encounter the following known issues, which may include workarounds, mitigation's, or expected resolution time-frames.

## Semantic Workbench App

### Error loading conversations: {"name":"BrowserAuthError","message":"hash_empty_error: Hash value cannot be processed because it is empty. Please verify that your redirectUri is not clearing the hash..."}

This error may appear when the access token for your login has expired and is not refreshing properly. More exploration is needed for the actual fix.

**Workaround**

1. If you encounter this error when using the Semantic Workbench app, please log out of the web app (upper right corner) and log back in.


=== File: Makefile ===
this_dir = $(patsubst %/,%,$(dir $(realpath $(lastword $(MAKEFILE_LIST)))))
include $(this_dir)/tools/makefiles/recursive.mk


=== File: README.md ===
# Semantic Workbench

Semantic Workbench is a versatile tool designed to help prototype intelligent assistants quickly.
It supports the creation of new assistants or the integration of existing ones, all within a
cohesive interface. The workbench provides a user-friendly UI for creating conversations with one
or more assistants, configuring settings, and exposing various behaviors.

The Semantic Workbench is composed of three main components:

- [Workbench Service](workbench-service/README.md) (Python): The backend service that
  handles core functionalities.
- [Workbench App](workbench-app/README.md) (React/Typescript): The frontend web user
  interface for interacting with workbench and assistants.
- [Assistant Services](examples) (Python, C#, etc.): any number of assistant services that implement the service protocols/APIs,
  developed using any framework and programming language of your choice.

Designed to be agnostic of any agent framework, language, or platform, the Semantic Workbench
facilitates experimentation, development, testing, and measurement of agent behaviors and workflows.
Assistants integrate with the workbench via a RESTful API, allowing for flexibility and broad applicability in various development environments.

![Semantic Workbench architecture](https://raw.githubusercontent.com/microsoft/semanticworkbench/main/docs/images/architecture-animation.gif)

# Workbench interface examples

![Configured dashboard example](docs/images/dashboard_configured_view.png)

![Prospector Assistant example](docs/images/prospector_example.png)

![Message debug inspection](docs/images/message_inspection.png)

![Mermaid graph example](examples/dotnet/dotnet-02-message-types-demo/docs/mermaid.png)

![ABC music example](examples/dotnet/dotnet-02-message-types-demo/docs/abc.png)

# Quick start (Recommended) - GitHub Codespaces for turn-key development environment

GitHub Codespaces provides a cloud-based development environment for your repository. It allows you to develop, build, and test your code
in a consistent environment, without needing to install dependencies or configure your local machine. It works with any system with a web
browser and internet connection, including Windows, MacOS, Linux, Chromebooks, tablets, and mobile devices.

See the [GitHub Codespaces / devcontainer README](.devcontainer/README.md) for more information on how to set up and use GitHub Codespaces
with Semantic Workbench.

## Local development environment

See the [setup guide](docs/SETUP_DEV_ENVIRONMENT.md) on how to configure your dev environment. Or if you have Docker installed you can use dev containers with VS Code which will function similarly to Codespaces.

## Using VS Code

Codespaces will is configured to use `semantic-workbench.code-workspace`, if you are working locally that is recommended over opening the repo root. This ensures that all project configurations, such as tools, formatters, and linters, are correctly applied in VS Code. This avoids issues like incorrect error reporting and non-functional tools.

Workspace files allow us to manage multiple projects within a monorepo more effectively. Each project can use its own virtual environment (venv), maintaining isolation and avoiding dependency conflicts. Multi-root workspaces (\*.code-workspace files) can point to multiple projects, each configured with its own Python interpreter, ensuring seamless functionality of Python tools and extensions.

### Start the app and service

- Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `semantic-workbench` to start the project
- Open your browser and navigate to `https://127.0.0.1:4000`
  - You may receive a warning about the app not being secure; click `Advanced` and `Proceed to localhost` to continue
- You can now interact with the app and service in the browser

### Start an assistant service:

- Launch an example an [example](examples/) assistant service:
  - No llm api keys needed
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-01-echo-bot` to start the example assistant that echos your messages. This is a good base to understand the basics of building your own assistant.
  - Bring your own llm api keys
    - Use VS Code > `Run and Debug` (Ctrl/Cmd+Shift+D) > `examples: python-02-simple-chatbot` to start the example chatbot assistant. Either set your keys in your .env file or after creating the assistant as described below, select it and provide the keys in the configuration page.

## Open the Workbench and create an Assistant

Open the app in your browser at [`https://localhost:4000`](https://localhost:4000). When you first log into the Semantic Workbench, follow these steps to get started:

1. **Create an Assistant**: On the dashboard, click the `New Assistant` button. Select a template from the available assistant services, provide a name, and click `Save`.

2. **Start a Conversation**: On the dashboard, click the `New Conversation` button. Provide a title for the conversation and click `Save`.

3. **Add the Assistant**: In the conversation window, click the conversation canvas icon and add your assistant to the conversation from the conversation canvas. Now you can converse with your assistant using the message box at the bottom of the conversation window.

   ![Open Conversation Canvas](docs/images/conversation_canvas_open.png)

   ![Open Canvas](docs/images/open_conversation_canvas.png)

Expected: You get a response from your assistant!

Note that the workbench provides capabilities that not all examples use, for example providing attachments. See the [Semantic Workbench](docs/WORKBENCH_APP.md) for more details.

# Developing your own assistants

To develop new assistants and connect existing ones, see the [Assistant Development Guide](docs/ASSISTANT_DEVELOPMENT_GUIDE.md) or any check out one of the [examples](examples).

- [Python example 1](examples/python/python-01-echo-bot/README.md): a simple assistant echoing text back.
- [Python example 2](examples/python/python-02-simple-chatbot/README.md): a simple chatbot implementing metaprompt guardrails and content moderation.
- [Python example 3](examples/python/python-03-multimodel-chatbot/README.md): an extension of the simple chatbot that supports configuration against additional llms.
- [.NET example 1](examples/dotnet/dotnet-01-echo-bot/README.md): a simple agent with echo and support for a basic `/say` command.
- [.NET example 2](examples/dotnet/dotnet-02-message-types-demo/README.md): a simple assistants showcasing Azure AI Content Safety integration and some workbench features like Mermaid graphs.
- [.NET example 3](examples/dotnet/dotnet-03-simple-chatbot/README.md): a functional chatbot implementing metaprompt guardrails and content moderation.

## Starting the workbench from the command line

- Run the script `tools\run-workbench-chatbot.sh` or `tools\run-workbench-chatbot.ps` which does the following:
  - Starts the backend service, see [here for instructions](workbench-service/README.md).
  - Starts the frontend app, see [here for instructions](workbench-app/README.md).
  - Starts the [Python chatbot example](examples/python/python-02-simple-chatbot/README.md)

## Refreshing Dev Environment

- Use the `tools\reset-service-data.sh` or `tools\reset-service-data.sh` script to reset all service data. You can also delete `~/workbench-service/.data` or specific files if you know which one(s).
- From repo root, run `make clean install`.
  - This will perform a `git clean` and run installs in all sub-directories
- Or a faster option if you just want to install semantic workbench related stuff:
  - From repo root, run `make clean`
  - From `~/workbench-app`, run `make install`
  - From `~/workbench-service`, run `make install`

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com>.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

Please see the detailed [contributing guide](CONTRIBUTING.md) for more information on how you can get involved.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

# Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.


=== File: RESPONSIBLE_AI_FAQ.md ===
# Semantic Workbench's Responsible AI FAQ

## What is Semantic Workbench?

- Semantic Workbench is a web application intended to help prototyping assistants during the development phase.
- Semantic Workbench provides a user interface for creating conversations with one or more assistants, including a configuration user interface, and a service to connect custom assistants.

## What is/are Semantic Workbench’s intended use(s)?

- Semantic Workbench is designed for prototyping assistants, running conversations and testing assistants behavior in a test environment.
- Semantic Workbench is not intended to be run in a production environment. AI assistants and agents developed with the help of Semantic Workbench, should be deployed separately from the workbench environment, in dedicated environments with proper monitoring and safety protections.

## How was Semantic Workbench evaluated? What metrics are used to measure performance?

Semantic Workbench has been built from the ground up specifically for the experimentation use-case. Other user interfaces and tools have been evaluated, but none allowed to prototype assistants decoupled from a specific underlying technology stack such as AI models or frameworks.

Semantic Workbench does not mandate any specific technology or framework.

Developers can use any of preferred technology and connect their bots to Semantic Workbench to benefit from its user interface, including configuration, debugging and visualization tools.

## What are the limitations of Semantic Workbench? How can users minimize the impact of Semantic Workbench’s limitations when using the system?

- Semantic Workbench is not an assistant in itself, it only allows to connect and test existing assistants.

- Semantic Workbench is not a container for Production assistants. Assistants and Agents are executed in the workbench environment only during development and test phases.

- Semantic Workbench does not monitor assistants behavior, it's only designed to make it easier for developers to observe the behavior. Developers are responsible for designing assistants and understanding if these are working properly.

- Intelligent assistants must be developed with usual IDEs and development tools like Semantic Kernel, Langchain, Autogen, following the best practices there recommended, for instance [Responsible AI and Semantic Kernel](https://learn.microsoft.com/semantic-kernel/when-to-use-ai/responsible-ai) and [LangSmith](https://www.langchain.com/langsmith).

- The workbench is unable to automatically discover agents: once the code for an agent is ready, some extra code needs to be added in order to connect the assistant to Semantic Workbench.

- Developers making use of the provided sample agents or connecting their own agents to Semantic Workbench are responsible for implementing security and safety into their agents, using, for example, [Azure AI Content Safety](https://azure.microsoft.com/eproducts/ai-services/ai-content-safety) and [Microsoft Purview](https://www.microsoft.com/security/business/microsoft-purview), and leveraging tools like [Responsible AI Toolbox](https://github.com/microsoft/responsible-ai-toolbox).

- When using Semantic Workbench to test an assistant, developers should carefully observe the bot’s behavior and use the debugging tools to investigate any unexpected outcomes. Although Semantic Workbench does not automatically detect harmful, inaccurate, or biased content, it enables developers to run and debug conversations, which helps identify and fix issues, improve the bot’s behavior, and edit prompts and code as necessary.

- Developers using Semantic Workbench can adopt a user-centric approach in designing applications, ensuring that users are well-informed and have the ability to approve any actions taken by the AI. Semantic Workbench exposes all the information provided by the connected assistants, so it's important that developers code these assistants to expose their rationale, prompts, and state.

- Additionally, intelligent assistants developers should implement mechanisms to monitor and filter any automatically generated information, if deemed necessary. Some of these mechanisms include:
  - moderating users' input and AI's output, for instance using [Azure AI Content Safety](https://azure.microsoft.com/products/ai-services/ai-content-safety).
  - including metaprompt guardrails, instructing LLMs how to protect users and business logic. For instance see [this page](https://learn.microsoft.com/azure/ai-services/openai/concepts/system-message) for information and examples.

- By addressing responsible AI issues in this manner, developers can create assistants that are not only efficient and useful but also adhere to ethical guidelines and prioritize user trust and safety.

## What operational factors and settings allow for effective and responsible use of Semantic Workbench?

- First and foremost, use Semantic Workbench to access your assistants only in private development environments, such as your localhost.

- Developers using Semantic Workbench can precisely define user interactions and how user data is managed in the source code of their intelligent assistants.

- If a prototype assistant runs a sequence of components, additional risks/failures may arise when using non-deterministic behavior. To mitigate this, developers can:

  - Implement safety measures and bounds on each component to prevent undesired outcomes.
  - Add output to the user to maintain control and awareness of the system's state.
  - In multi-agent scenarios, build in places that prompt the user for a response, ensuring user involvement and reducing the likelihood of undesired results due to multi-agent looping.

- When working with AI, the developer can enable content moderation in the AI platforms used, and has complete control on the prompts being used, including the ability to define responsible boundaries and guidelines. For instance:

  - When using Azure OpenAI, by default the service includes a content filtering system that works alongside core models. This system works by running both the prompt and completion through an ensemble of classification models aimed at detecting and preventing the output of harmful content. In addition to the content filtering system, the Azure OpenAI Service performs monitoring to detect content and/or behaviors that suggest use of the service in a manner that might violate applicable product terms. The filter configuration can be adjusted, for example to block also "low severity level" content. See [here](https://learn.microsoft.com/azure/ai-services/openai/concepts/content-filter) for more information.

  - The developer can integrate Azure AI Content Safety to detect harmful user-generated and AI-generated content, including text and images. The service includes an interactive Studio online tool with templates and customized workflows. See [here](https://learn.microsoft.com/azure/ai-services/content-safety) for more information.

  - When using OpenAI the developer can integrate OpenAI Moderation to identify problematic content and take action, for instance by filtering it. See [here](https://platform.openai.com/docs/guides/moderation) for more information.

  - Other AI providers provide content moderation and moderation APIs, which developers can integrate with Node Engine.


=== File: SECURITY.md ===
## Security

Microsoft takes the security of our software products and services seriously, which includes all source code repositories managed through our GitHub organizations, which include [Microsoft](https://github.com/Microsoft), [Azure](https://github.com/Azure), [DotNet](https://github.com/dotnet), [AspNet](https://github.com/aspnet) and [Xamarin](https://github.com/xamarin).

If you believe you have found a security vulnerability in any Microsoft-owned repository that meets [Microsoft's definition of a security vulnerability](https://aka.ms/security.md/definition), please report it to us as described below.

## Reporting Security Issues

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them to the Microsoft Security Response Center (MSRC) at [https://msrc.microsoft.com/create-report](https://aka.ms/security.md/msrc/create-report).

If you prefer to submit without logging in, send email to [secure@microsoft.com](mailto:secure@microsoft.com).  If possible, encrypt your message with our PGP key; please download it from the [Microsoft Security Response Center PGP Key page](https://aka.ms/security.md/msrc/pgp).

You should receive a response within 24 hours. If for some reason you do not, please follow up via email to ensure we received your original message. Additional information can be found at [microsoft.com/msrc](https://www.microsoft.com/msrc). 

Please include the requested information listed below (as much as you can provide) to help us better understand the nature and scope of the possible issue:

  * Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
  * Full paths of source file(s) related to the manifestation of the issue
  * The location of the affected source code (tag/branch/commit or direct URL)
  * Any special configuration required to reproduce the issue
  * Step-by-step instructions to reproduce the issue
  * Proof-of-concept or exploit code (if possible)
  * Impact of the issue, including how an attacker might exploit the issue

This information will help us triage your report more quickly.

If you are reporting for a bug bounty, more complete reports can contribute to a higher bounty award. Please visit our [Microsoft Bug Bounty Program](https://aka.ms/security.md/msrc/bounty) page for more details about our active programs.

## Preferred Languages

We prefer all communications to be in English.

## Policy

Microsoft follows the principle of [Coordinated Vulnerability Disclosure](https://aka.ms/security.md/cvd).


=== File: SUPPORT.md ===
# Support

## How to file issues and get help  

This project uses GitHub Issues to track bugs and feature requests. Please search the existing 
issues before filing new issues to avoid duplicates.  For new issues, file your bug or 
feature request as a new Issue.

For help and questions about using this project, please create a new GitHub Issue with your request.

## Microsoft Support Policy  

Support for this project is limited to the resources listed above.


=== File: ruff.toml ===
line-length = 120
target-version = "py311"

[format]
docstring-code-format = true
line-ending = "lf"
preview = true


