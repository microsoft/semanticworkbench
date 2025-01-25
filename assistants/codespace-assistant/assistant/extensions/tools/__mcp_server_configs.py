from textwrap import dedent
from typing import List

from .__model import MCPServerConfig

# List of MCP server configurations
# Each configuration includes the server name, command, arguments, and environment variables.
# Tested with 'npx' commands and _should_ work with 'uvx' as well.
# Can also use 'node' (and probably 'python'), but requires the full path to the lib/script called.

mcp_server_configs: List[MCPServerConfig] = [
    MCPServerConfig(
        name="Filesystem MCP Server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/workspaces/semanticworkbench"],
    ),
    MCPServerConfig(
        name="Memory MCP Server",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-memory"],
        prompt=dedent("""
            Follow these steps for each interaction:

            1. User Identification:
            - You should assume that you are interacting with default_user
            - If you have not identified default_user, proactively try to do so.

            2. Memory Retrieval:
            - Always begin your chat by saying only "Remembering..." and retrieve all relevant information from your knowledge graph
            - Always refer to your knowledge graph as your "memory"

            3. Memory
            - While conversing with the user, be attentive to any new information that falls into these categories:
                a) Basic Identity (age, gender, location, job title, education level, etc.)
                b) Behaviors (interests, habits, etc.)
                c) Preferences (communication style, preferred language, etc.)
                d) Goals (goals, targets, aspirations, etc.)
                e) Relationships (personal and professional relationships up to 3 degrees of separation)

            4. Memory Update:
            - If any new information was gathered during the interaction, update your memory as follows:
                a) Create entities for recurring organizations, people, and significant events
                b) Connect them to the current entities using relations
                b) Store facts about them as observations
        """),
    ),
    MCPServerConfig(
        name="Web Research MCP Server",
        command="npx",
        args=["-y", "@mzxrai/mcp-webresearch@latest"],
    ),
]
