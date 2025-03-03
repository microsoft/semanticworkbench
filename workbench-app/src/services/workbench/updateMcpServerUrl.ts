// Copyright (c) Microsoft. All rights reserved.

import { getVSCodeMcpServerUrl } from './mcpServerUrl';

/**
 * Interface representing an MCP server configuration
 */
interface McpServerConfig {
    enabled: boolean;
    key: string;
    command: string;
    args: string[];
    env: Record<string, string>[];
    prompt: string;
    long_running: boolean;
    task_completion_estimate: number;
}

/**
 * Updates the VSCode MCP server URL in the assistant configuration
 *
 * @param assistantConfig The assistant configuration object
 * @returns The updated assistant configuration object
 */
export function updateVSCodeMcpServerUrl(assistantConfig: any): any {
    // Make a deep copy of the configuration to avoid modifying the original
    const updatedConfig = JSON.parse(JSON.stringify(assistantConfig));

    // Check if the configuration has the extensions_config.tools.mcp_servers property
    if (
        updatedConfig?.extensions_config?.tools?.mcp_servers &&
        Array.isArray(updatedConfig.extensions_config.tools.mcp_servers)
    ) {
        // Get the dynamic VSCode MCP server URL
        const dynamicUrl = getVSCodeMcpServerUrl();

        if (dynamicUrl) {
            // Find the VSCode MCP server in the configuration
            const vscodeServerIndex = updatedConfig.extensions_config.tools.mcp_servers.findIndex(
                (server: McpServerConfig) => server.key === 'vscode',
            );

            if (vscodeServerIndex !== -1) {
                // Update the command with the dynamic URL
                updatedConfig.extensions_config.tools.mcp_servers[vscodeServerIndex].command = dynamicUrl;
            }
        }
    }

    return updatedConfig;
}

/**
 * Updates the VSCode MCP server URL in the assistant configuration string
 *
 * @param assistantConfigString The assistant configuration as a JSON string
 * @returns The updated assistant configuration as a JSON string
 */
export function updateVSCodeMcpServerUrlInString(assistantConfigString: string): string {
    try {
        // Parse the configuration string
        const config = JSON.parse(assistantConfigString);

        // Update the configuration
        const updatedConfig = updateVSCodeMcpServerUrl(config);

        // Stringify the updated configuration
        return JSON.stringify(updatedConfig, null, 2);
    } catch (error) {
        console.error('Error updating VSCode MCP server URL in string:', error);
        return assistantConfigString;
    }
}
