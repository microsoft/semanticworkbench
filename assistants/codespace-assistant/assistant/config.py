from textwrap import dedent
from typing import Annotated

from assistant_extensions.ai_clients.config import (
    AzureOpenAIClientConfigModel,
    OpenAIClientConfigModel,
)
from assistant_extensions.attachments import AttachmentsConfigModel
from assistant_extensions.mcp import HostedMCPServerConfig, MCPClientRoot, MCPServerConfig
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from openai_client import (
    OpenAIRequestConfig,
    azure_openai_service_config_construct,
    azure_openai_service_config_reasoning_construct,
)
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema, first_env_var

from . import helpers

# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


#
# region Assistant Configuration
#


class ExtensionsConfigModel(BaseModel):
    attachments: Annotated[
        AttachmentsConfigModel,
        Field(
            title="Attachments Extension",
            description="Configuration for the attachments extension.",
        ),
    ] = AttachmentsConfigModel()


class PromptsConfigModel(BaseModel):
    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description=dedent("""
                The prompt used to instruct the behavior and capabilities of the AI assistant and any preferences.
            """).strip(),
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("instruction_prompt.txt")

    guidance_prompt: Annotated[
        str,
        Field(
            title="Guidance Prompt",
            description=dedent("""
                The prompt used to provide a structured set of instructions to carry out a specific workflow
                from start to finish. It should outline a clear, step-by-step process for gathering necessary
                context, breaking down the objective into manageable components, executing the defined steps,
                and validating the results.
            """).strip(),
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("guidance_prompt.txt")

    guardrails_prompt: Annotated[
        str,
        Field(
            title="Guardrails Prompt",
            description=(
                "The prompt used to inform the AI assistant about the guardrails to follow. Default value based upon"
                " recommendations from: [Microsoft OpenAI Service: System message templates]"
                "(https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/system-message"
                "#define-additional-safety-and-behavioral-guardrails)"
            ),
        ),
        UISchema(widget="textarea", enable_markdown_in_description=True),
    ] = helpers.load_text_include("guardrails_prompt.txt")


class ResponseBehaviorConfigModel(BaseModel):
    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
        UISchema(widget="textarea"),
    ] = (
        "Hello! I am an assistant that can help you with coding projects within the context of the Semantic Workbench."
        "Let's get started by having a conversation about your project. You can ask me questions, request code"
        " snippets, or ask for help with debugging. I can also help you with markdown, code snippets, and other types"
        " of content. You can also attach .docx, text, and image files to your chat messages to help me better"
        " understand the context of our conversation. Where would you like to start?"
    )

    only_respond_to_mentions: Annotated[
        bool,
        Field(
            title="Only Respond to @Mentions",
            description="Only respond to messages that @mention the assistant.",
        ),
    ] = False


class HostedMCPServersConfigModel(BaseModel):
    web_research: Annotated[
        HostedMCPServerConfig,
        Field(
            title="Web Research",
            description="Enable your assistant to perform web research on a given topic. It will generate a list of facts it needs to collect and use Bing search and simple web requests to fill in the facts. Once it decides it has enough, it will summarize the information and return it as a report.",
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env("web-research", "MCP_SERVER_WEB_RESEARCH_URL")

    open_deep_research_clone: Annotated[
        HostedMCPServerConfig,
        Field(
            title="Open Deep Research Clone",
            description="Enable a web research tool that is modeled after the Open Deep Research project as a demonstration of writing routines using our Skills library.",
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env("open-deep-research-clone", "MCP_SERVER_OPEN_DEEP_RESEARCH_CLONE_URL", False)

    giphy: Annotated[
        HostedMCPServerConfig,
        Field(
            title="Giphy",
            description="Enable your assistant to search for and share GIFs from Giphy.",
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env("giphy", "MCP_SERVER_GIPHY_URL")

    memory_user_bio: Annotated[
        HostedMCPServerConfig,
        Field(
            title="User-Bio Memories",
            description=dedent("""
                Enable this assistant to store long-term memories about you, the user (\"user-bio\" memories).
                This implementation is modeled after ChatGPT's memory system.
                These memories are available to the assistant in all conversations, much like ChatGPT memories are available
                to ChatGPT in all chats.
                To determine what memories are saved, you can ask the assistant what memories it has of you.
                To forget a memory, you can ask the assistant to forget it.
                """).strip(),
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env(
        "memory-user-bio",
        "MCP_SERVER_MEMORY_USER_BIO_URL",
        # scopes the memories to the assistant instance
        roots=[MCPClientRoot(name="session-id", uri="file://{assistant_id}")],
        # auto-include the user-bio memory prompt
        prompts_to_auto_include=["user-bio"],
        enabled=False,
    )

    filesystem_edit: Annotated[
        HostedMCPServerConfig,
        Field(
            title="Document Editor",
            description=dedent("""
                Enable this to create, edit, and refine markdown (*.md) documents, all through chat
                """).strip(),
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env(
        "filesystem-edit",
        "MCP_SERVER_FILESYSTEM_EDIT_URL",
        # configures the filesystem edit server to use the client-side storage (using the magic hostname of "workspace")
        roots=[MCPClientRoot(name="root", uri="file://workspace/")],
        prompts_to_auto_include=["instructions"],
        enabled=False,
    )

    @property
    def mcp_servers(self) -> list[HostedMCPServerConfig]:
        """
        Returns a list of all hosted MCP servers that are configured.
        """
        # Get all fields that are of type HostedMCPServerConfig
        configs = [
            getattr(self, field)
            for field in self.model_fields
            if isinstance(getattr(self, field), HostedMCPServerConfig)
        ]
        # Filter out any configs that are missing command (URL)
        return [config for config in configs if config.command]


class AdvancedToolConfigModel(BaseModel):
    max_steps: Annotated[
        int,
        Field(
            title="Maximum Steps",
            description="The maximum number of steps to take when using tools, to avoid infinite loops.",
        ),
    ] = 50

    max_steps_truncation_message: Annotated[
        str,
        Field(
            title="Maximum Steps Truncation Message",
            description="The message to display when the maximum number of steps is reached.",
        ),
    ] = "[ Maximum steps reached for this turn, engage with assistant to continue ]"

    additional_instructions: Annotated[
        str,
        Field(
            title="Tools Instructions",
            description=dedent("""
                General instructions for using tools.  No need to include a list of tools or instruction
                on how to use them in general, that will be handled automatically.  Instead, use this
                space to provide any additional instructions for using specific tools, such folders to
                exclude in file searches, or instruction to always re-read a file before using it.
            """).strip(),
        ),
        UISchema(widget="textarea", enable_markdown_in_description=True),
    ] = dedent("""
        - Use the available tools to assist with specific tasks.
        - Before performing any file operations, use the `list_allowed_directories` tool to get a list of directories
            that are allowed for file operations. Always use paths relative to an allowed directory.
        - When searching or browsing for files, consider the kinds of folders and files that should be avoided:
            - For example, for coding projects exclude folders like `.git`, `.vscode`, `node_modules`, and `dist`.
        - For each turn, always re-read a file before using it to ensure the most up-to-date information, especially
            when writing or editing files.
        - The search tool does not appear to support wildcards, but does work with partial file names.
    """).strip()

    tools_disabled: Annotated[
        list[str],
        Field(
            title="Disabled Tools",
            description=dedent("""
                List of individual tools to disable. Use this if there is a problem tool that you do not want
                made visible to your assistant.
            """).strip(),
        ),
    ] = ["directory_tree"]


class MCPToolsConfigModel(BaseModel):
    enabled: Annotated[
        bool,
        Field(title="Enable experimental use of tools"),
    ] = True

    hosted_mcp_servers: Annotated[
        HostedMCPServersConfigModel,
        Field(
            title="Hosted MCP Servers",
            description="Configuration for hosted MCP servers that provide tools to the assistant.",
        ),
        UISchema(collapsed=False, items=UISchema(title_fields=["key", "enabled"])),
    ] = HostedMCPServersConfigModel()

    personal_mcp_servers: Annotated[
        list[MCPServerConfig],
        Field(
            title="Personal MCP Servers",
            description="Configuration for personal MCP servers that provide tools to the assistant.",
        ),
        UISchema(items=UISchema(collapsible=False, hide_title=True, title_fields=["key", "enabled"])),
    ] = [
        MCPServerConfig(
            key="filesystem",
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "/workspaces/semanticworkbench",
            ],
            enabled=False,
        ),
        MCPServerConfig(
            key="vscode",
            command="http://127.0.0.1:6010/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="bing-search",
            command="http://127.0.0.1:6030/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="giphy",
            command="http://127.0.0.1:6040/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="fusion",
            command="http://127.0.0.1:6050/sse",
            args=[],
            prompt=dedent("""
                When creating models using the Fusion tool suite, keep these guidelines in mind:

                - **Coordinate System & Planes:**
                - **Axes:** Z is vertical, X is horizontal, and Y is depth.
                - **Primary Planes:**
                    - **XY:** Represents top and bottom surfaces (use the top or bottom Z coordinate as needed).
                    - **XZ:** Represents the front and back surfaces (use the appropriate Y coordinate).
                    - **YZ:** Represents the left and right surfaces (use the appropriate X coordinate).

                - **Sketch & Geometry Management:**
                - **Sketch Creation:** Always create or select the proper sketch using `create_sketch` or `create_sketch_on_offset_plane` before adding geometry. This ensures the correct reference plane is used.
                - **Top-Face Features:** For features intended for the top surface (like button openings), use `create_sketch_on_offset_plane` with an offset equal to the block's height and confirm the sketch is positioned at the correct Z value.
                - **Distinct Sketches for Operations:** Use separate sketches for base extrusions and cut operations (e.g., avoid reusing the same sketch for both extrude and cut_extrude) to maintain clarity and prevent unintended geometry modifications.
                - **Validation:** Use the `sketches` tool to list available sketches and confirm names before referencing them in other operations.

                - **Feature Operations & Parameters:**
                - **Extrude vs. Cut:** When using extrude operations, verify that the direction vector is correctly defined (defaults to positive Z if omitted) and that distances (extrusion or cut depth) are positive.
                - **Cut Direction for Top-Face Features:** When cutting features from the top face, ensure the extrusion (cut) direction is set to [0, 0, -1] so that the cut is made downward from the top surface.
                - **Targeting Entities:** For operations like `cut_extrude` and `rectangular_pattern`, ensure the entity names provided refer to existing, valid bodies.
                - **Adjustment Consideration:** Always consider the required adjustment on the third axis (depth for XY-based operations, etc.) to maintain proper alignment and avoid unintended modifications.

                By following these guidelines, you help ensure that operations are applied to the correct geometry and that the overall modeling process remains stable and predictable.
            """).strip(),
            enabled=False,
        ),
        MCPServerConfig(
            key="memory",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-memory"],
            prompt=dedent("""
                Follow these steps for each interaction:

                1. Memory Retrieval:
                - Always begin your chat by saying only "Remembering..." and retrieve all relevant information
                  from your knowledge graph
                - Always refer to your knowledge graph as your "memory"

                2. Memory
                - While conversing with the user, be attentive to any new information that falls into these categories:
                    a) Basic Identity (age, gender, location, job title, education level, etc.)
                    b) Behaviors (interests, habits, etc.)
                    c) Preferences (communication style, preferred language, etc.)
                    d) Goals (goals, targets, aspirations, etc.)
                    e) Relationships (personal and professional relationships up to 3 degrees of separation)

                3. Memory Update:
                - If any new information was gathered during the interaction, update your memory as follows:
                    a) Create entities for recurring organizations, people, and significant events
                    b) Connect them to the current entities using relations
                    b) Store facts about them as observations
            """).strip(),
            enabled=False,
        ),
        MCPServerConfig(
            key="sequential-thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
            enabled=False,
        ),
        MCPServerConfig(
            key="open-deep-research",
            command="http://127.0.0.1:6020/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="open-deep-research-clone-personal",
            command="http://127.0.0.1:6061/sse",
            args=[],
            enabled=False,
        ),
        MCPServerConfig(
            key="web-research-personal",
            command="http://127.0.0.1:6060/sse",
            args=[],
            enabled=False,
        ),
    ]

    advanced: Annotated[
        AdvancedToolConfigModel,
        Field(
            title="Advanced Tool Settings",
        ),
    ] = AdvancedToolConfigModel()

    @property
    def mcp_servers(self) -> list[MCPServerConfig]:
        """
        Returns a list of all MCP servers, including both hosted and personal configurations.
        """
        return self.hosted_mcp_servers.mcp_servers + self.personal_mcp_servers


# the workbench app builds dynamic forms based on the configuration model and UI schema
class AssistantConfigModel(BaseModel):
    tools: Annotated[
        MCPToolsConfigModel,
        Field(
            title="Tools",
        ),
        UISchema(collapsed=False, items=UISchema(schema={"hosted_mcp_servers": {"ui:options": {"collapsed": False}}})),
    ] = MCPToolsConfigModel()

    extensions_config: Annotated[
        ExtensionsConfigModel,
        Field(
            title="Assistant Extensions",
        ),
    ] = ExtensionsConfigModel()

    prompts: Annotated[
        PromptsConfigModel,
        Field(
            title="Prompts",
            description="Configuration for various prompts used by the assistant.",
        ),
    ] = PromptsConfigModel()

    response_behavior: Annotated[
        ResponseBehaviorConfigModel,
        Field(
            title="Response Behavior",
            description="Configuration for the response behavior of the assistant.",
        ),
    ] = ResponseBehaviorConfigModel()

    generative_ai_client_config: Annotated[
        AzureOpenAIClientConfigModel | OpenAIClientConfigModel,
        Field(
            title="OpenAI Generative Model",
            description="Configuration for the generative model, such as gpt-4o.",
            discriminator="ai_service_type",
            default=AzureOpenAIClientConfigModel.model_construct(),
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIClientConfigModel(
        service_config=azure_openai_service_config_construct(),
        request_config=OpenAIRequestConfig(
            max_tokens=128_000,
            response_tokens=16_384,
            model="gpt-4o",
            is_reasoning_model=False,
        ),
    )

    reasoning_ai_client_config: Annotated[
        AzureOpenAIClientConfigModel | OpenAIClientConfigModel,
        Field(
            title="OpenAI Reasoning Model",
            description="Configuration for the reasoning model, such as o1, o1-preview, o1-mini, etc.",
            discriminator="ai_service_type",
            default=AzureOpenAIClientConfigModel.model_construct(),
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIClientConfigModel(
        service_config=azure_openai_service_config_reasoning_construct(),
        request_config=OpenAIRequestConfig(
            max_tokens=200_000,
            response_tokens=65_536,
            model=first_env_var(
                "azure_openai_reasoning_model",
                "assistant__azure_openai_reasoning_model",
                "azure_openai_model",
                "assistant__azure_openai_model",
            )
            or "o3-mini",
            is_reasoning_model=True,
            reasoning_effort="high",
        ),
    )

    content_safety_config: Annotated[
        CombinedContentSafetyEvaluatorConfig,
        Field(
            title="Content Safety",
        ),
        UISchema(widget="radio"),
    ] = CombinedContentSafetyEvaluatorConfig()

    # add any additional configuration fields


class WorkspaceMCPToolsConfigModel(MCPToolsConfigModel):
    personal_mcp_servers: Annotated[
        list[MCPServerConfig],
        Field(
            title="Personal MCP Servers",
            description="Configuration for personal MCP servers that provide tools to the assistant.",
        ),
        UISchema(items=UISchema(collapsible=False, hide_title=True, title_fields=["key", "enabled"])),
    ] = []


class WorkspacePromptsConfigModel(PromptsConfigModel):
    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior and capabilities of the AI assistant and any preferences.",
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("instruction_prompt_workspace.txt")

    guidance_prompt: Annotated[
        str,
        Field(
            title="Guidance Prompt",
            description="The prompt used to provide a structured set of instructions to carry out a specific workflow from start to finish.",
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("guidance_prompt_workspace.txt")

    guardrails_prompt: Annotated[
        str,
        Field(
            title="Guardrails Prompt",
            description="The prompt used to inform the AI assistant about the guardrails to follow.",
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("guardrails_prompt_workspace.txt")


class WorkspaceAssistantConfigModel(AssistantConfigModel):
    tools: Annotated[
        MCPToolsConfigModel,
        Field(
            title="Tools",
        ),
        UISchema(collapsed=False, items=UISchema(schema={"hosted_mcp_servers": {"ui:options": {"collapsed": False}}})),
    ] = WorkspaceMCPToolsConfigModel()

    prompts: Annotated[
        PromptsConfigModel,
        Field(
            title="Prompts",
        ),
    ] = WorkspacePromptsConfigModel()


class ContextTransferPromptsConfigModel(PromptsConfigModel):
    instruction_prompt: Annotated[
        str,
        Field(
            title="Instruction Prompt",
            description="The prompt used to instruct the behavior and capabilities of the AI assistant and any preferences.",
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("instruction_prompt_context_transfer.txt")

    guidance_prompt: Annotated[
        str,
        Field(
            title="Guidance Prompt",
            description="The prompt used to provide a structured set of instructions to carry out a specific workflow from start to finish.",
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("guidance_prompt_context_transfer.txt")

    guardrails_prompt: Annotated[
        str,
        Field(
            title="Guardrails Prompt",
            description="The prompt used to inform the AI assistant about the guardrails to follow.",
        ),
        UISchema(widget="textarea"),
    ] = helpers.load_text_include("guardrails_prompt_workspace.txt")


class ContextTransferConfigModel(WorkspaceAssistantConfigModel):
    prompts: Annotated[
        PromptsConfigModel,
        Field(
            title="Prompts",
        ),
    ] = ContextTransferPromptsConfigModel()


# endregion
