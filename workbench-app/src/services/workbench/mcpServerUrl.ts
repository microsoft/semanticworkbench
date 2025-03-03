/**
 * This file defines the global variable for the VSCode MCP server URL and provides
 * functions to access and update it.
 */

// Default VSCode MCP server URL when no custom URL is provided
const DEFAULT_VSCODE_MCP_SERVER_URL = 'http://127.0.0.1:6010/sse';

// Global variable to store the current VSCode MCP server URL
let vscodeMcpServerUrl: string = DEFAULT_VSCODE_MCP_SERVER_URL;

/**
 * Get the current VSCode MCP server URL
 * @returns The current VSCode MCP server URL, or the default URL if not set
 */
export function getMcpServerUrl(): string {
    return vscodeMcpServerUrl || DEFAULT_VSCODE_MCP_SERVER_URL;
}

/**
 * Set the VSCode MCP server URL
 * @param url The new VSCode MCP server URL
 */
export function setMcpServerUrl(url: string): void {
    if (!url) {
        console.warn('Attempted to set VSCode MCP server URL to empty or null value');
        return;
    }

    // Only update if the URL has changed
    if (url !== vscodeMcpServerUrl) {
        console.log(`Updating VSCode MCP server URL from ${vscodeMcpServerUrl} to ${url}`);
        vscodeMcpServerUrl = url;
    }
}

/**
 * Reset the VSCode MCP server URL to the default value
 */
export function resetMcpServerUrl(): void {
    console.log(`Resetting VSCode MCP server URL to default: ${DEFAULT_VSCODE_MCP_SERVER_URL}`);
    vscodeMcpServerUrl = DEFAULT_VSCODE_MCP_SERVER_URL;
}
