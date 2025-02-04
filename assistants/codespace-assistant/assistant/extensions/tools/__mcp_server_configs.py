from textwrap import dedent
from typing import List

from .__model import MCPServerConfig, ToolsConfigModel

# List of MCP server configurations
# Each configuration includes the server name, command, arguments, and environment variables.
# Tested with 'npx' commands and _should_ work with 'uvx' as well.
# Can also use 'node' (and probably 'python'), but requires the full path to the lib/script called.
# The 'key' is used to identify the server in config, logs, etc.


def get_mcp_server_configs(tools_config: ToolsConfigModel) -> List[MCPServerConfig]:
    return [
        MCPServerConfig(
            key="filesystem",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-filesystem", *tools_config.file_system_paths],
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
        """),
        ),
        MCPServerConfig(
            key="coder",
            command="http://127.0.0.1:6010/sse",
            args=[
                *tools_config.file_system_paths,
            ],
        ),
        MCPServerConfig(
            key="giphy",
            command="http://127.0.0.1:6000/sse",
            args=[],
        ),
        MCPServerConfig(
            key="sequential_thinking",
            command="npx",
            args=["-y", "@modelcontextprotocol/server-sequential-thinking"],
        ),
        # MCPServerConfig(
        #     name="Web Research MCP Server",
        #     command="npx",
        #     args=["-y", "@mzxrai/mcp-webresearch@latest"],
        # ),
    ]
