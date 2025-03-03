/**
 * This file provides functions to update the VSCode MCP server URL in the assistant configuration.
 */

import { getMcpServerUrl } from './mcpServerUrl';

/**
 * Interface for an MCP server configuration in the assistant config
 */
interface MCPServerConfig {
    key: string;
    command: string;
    args: string[];
    enabled?: boolean;
    [key: string]: any;
}

/**
 * Interface for an assistant configuration that includes MCP servers
 */
interface AssistantConfig {
    mcpServers?: MCPServerConfig[];
    [key: string]: any;
}

/**
 * Update the VSCode MCP server URL in an assistant configuration
 * @param config The assistant configuration to update
 * @param url Optional URL to use (defaults to the current global URL)
 * @returns A new configuration with the updated URL
 */
export function updateConfigWithMcpServerUrl(config: AssistantConfig, url?: string): AssistantConfig {
    // Use the provided URL or get the current one from the global state
    const mcpServerUrl = url || getMcpServerUrl();

    // If there's no config or no mcpServers array, return the original config
    if (!config || !config.mcpServers) {
        return config;
    }

    // Create a deep copy of the configuration to avoid mutations
    const updatedConfig = JSON.parse(JSON.stringify(config));

    // Find and update the VSCode MCP server in the configuration
    const updatedServers = updatedConfig.mcpServers.map((server: MCPServerConfig) => {
        if (server.key === 'vscode') {
            return {
                ...server,
                command: mcpServerUrl,
            };
        }
        return server;
    });

    updatedConfig.mcpServers = updatedServers;
    return updatedConfig;
}

/**
 * Check if a configuration has a VSCode MCP server configured
 * @param config The assistant configuration to check
 * @returns True if the configuration has a VSCode MCP server, false otherwise
 */
export function hasVscodeMcpServer(config: AssistantConfig): boolean {
    if (!config || !config.mcpServers) {
        return false;
    }

    return config.mcpServers.some((server: MCPServerConfig) => server.key === 'vscode');
}

/**
 * Get the current VSCode MCP server configuration
 * @param config The assistant configuration to check
 * @returns The VSCode MCP server configuration, or undefined if not found
 */
export function getVscodeMcpServerConfig(config: AssistantConfig): MCPServerConfig | undefined {
    if (!config || !config.mcpServers) {
        return undefined;
    }

    return config.mcpServers.find((server: MCPServerConfig) => server.key === 'vscode');
}
