from textwrap import dedent
from typing import Annotated

from assistant_extensions.ai_clients.config import AzureOpenAIClientConfigModel, OpenAIClientConfigModel
from assistant_extensions.mcp import HostedMCPServerConfig, MCPClientRoot, MCPServerConfig
from content_safety.evaluators import CombinedContentSafetyEvaluatorConfig
from openai_client import (
    OpenAIRequestConfig,
    azure_openai_service_config_construct,
    azure_openai_service_config_reasoning_construct,
)
from pydantic import BaseModel, Field
from semantic_workbench_assistant.config import UISchema

from assistant.filesystem import AttachmentsConfigModel
from assistant.guidance.guidance_config import GuidanceConfigModel

from . import helpers

# The semantic workbench app uses react-jsonschema-form for rendering
# dynamic configuration forms based on the configuration model and UI schema
# See: https://rjsf-team.github.io/react-jsonschema-form/docs/
# Playground / examples: https://rjsf-team.github.io/react-jsonschema-form/

# The UI schema can be used to customize the appearance of the form. Use
# the UISchema class to define the UI schema for specific fields in the
# configuration model.


class ExtensionsConfigModel(BaseModel):
    attachments: Annotated[
        AttachmentsConfigModel,
        Field(
            title="Attachments Extension",
            description="Configuration for the attachments extension.",
        ),
    ] = AttachmentsConfigModel()

    guidance: Annotated[
        GuidanceConfigModel,
        Field(
            title="User Guidance",
            description="Enables user guidance including dynamic UI generation for user preferences",
        ),
    ] = GuidanceConfigModel()


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
    ] = helpers.load_text_include("instruction_prompt_document.txt")

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
    ] = helpers.load_text_include("guidance_prompt_document.txt")

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
    ] = helpers.load_text_include("guardrails_prompt_document.txt")


class ResponseBehaviorConfigModel(BaseModel):
    welcome_message: Annotated[
        str,
        Field(
            title="Welcome Message",
            description="The message to display when the conversation starts.",
        ),
        UISchema(widget="textarea"),
    ] = dedent("""
               Welcome to your new document assistant! Here are ideas for how to get started:
                - ⚙️ Tell me what you are working on, such as *I'm working on creating a new budget process*
                - 🗃️ Upload files you are working with and I'll take it from there
                - 📝 I can make you an initial draft like *Write a proposal for new project management software in our department*
                - 🧪 Ask me to conduct research for example, *Find me the latest competitors in the wearables market*
               """).strip()

    only_respond_to_mentions: Annotated[
        bool,
        Field(
            title="Only Respond to @Mentions",
            description="Only respond to messages that @mention the assistant.",
        ),
    ] = False


class HostedMCPServersConfigModel(BaseModel):
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
    )

    web_research: Annotated[
        HostedMCPServerConfig,
        Field(
            title="Web Research",
            description="Enable your assistant to perform web research on a given topic. It will generate a list of facts it needs to collect and use Bing search and simple web requests to fill in the facts. Once it decides it has enough, it will summarize the information and return it as a report.",
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env("web-research", "MCP_SERVER_WEB_RESEARCH_URL", True)

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
    )

    memory_whiteboard: Annotated[
        HostedMCPServerConfig,
        Field(
            title="Whiteboard Memory",
            description=dedent("""
                Enable this assistant to retain memories of active and historical tasks and decisions, in the form of a whiteboard.
                Whiteboards are scoped to the conversation.
                """).strip(),
        ),
        UISchema(collapsible=False),
    ] = HostedMCPServerConfig.from_env(
        "memory-whiteboard",
        "MCP_SERVER_MEMORY_WHITEBOARD_URL",
        # scopes the memories to this conversation for this assistant
        roots=[MCPClientRoot(name="session-id", uri="file://{assistant_id}.{conversation_id}")],
        # auto-include the whiteboard memory prompt
        prompts_to_auto_include=["memory:whiteboard"],
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
    ] = 15

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
    ] = ""

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
    ] = []

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
            discriminator="ai_service_type",
            default=AzureOpenAIClientConfigModel.model_construct(),
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIClientConfigModel(
        service_config=azure_openai_service_config_construct(default_deployment="gpt-4.1"),
        request_config=OpenAIRequestConfig(
            max_tokens=128_000,
            response_tokens=16_384,
            model="gpt-4.1",
            is_reasoning_model=False,
        ),
    )

    reasoning_ai_client_config: Annotated[
        AzureOpenAIClientConfigModel | OpenAIClientConfigModel,
        Field(
            title="OpenAI Reasoning Model",
            discriminator="ai_service_type",
            default=AzureOpenAIClientConfigModel.model_construct(),
        ),
        UISchema(widget="radio", hide_title=True),
    ] = AzureOpenAIClientConfigModel(
        service_config=azure_openai_service_config_reasoning_construct(default_deployment="o3-mini"),
        request_config=OpenAIRequestConfig(
            max_tokens=200_000,
            response_tokens=65_536,
            model="o3-mini",
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
