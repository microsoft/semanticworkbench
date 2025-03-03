// Copyright (c) Microsoft. All rights reserved.

/**
 * Gets the VSCode MCP server URL from the global variable set by the VSCode MCP server extension.
 * This allows the semantic workbench to dynamically pull the URL from VSCode's output.
 *
 * @returns The VSCode MCP server URL or undefined if not available
 */
export function getVSCodeMcpServerUrl(): string | undefined {
    // Check if we're in a browser environment with access to the global variable
    if (typeof window !== 'undefined' && (window as any).__VSCODE_MCP_SERVER_URL) {
        return (window as any).__VSCODE_MCP_SERVER_URL;
    }

    // Check if we're in a Node.js environment with access to the global variable
    if (typeof global !== 'undefined' && (global as any).__VSCODE_MCP_SERVER_URL) {
        return (global as any).__VSCODE_MCP_SERVER_URL;
    }

    // If the global variable is not available, return undefined
    return undefined;
}

/**
 * Gets the VSCode MCP server URL from the global variable or falls back to a default URL.
 *
 * @param defaultUrl The default URL to use if the global variable is not available
 * @returns The VSCode MCP server URL or the default URL
 */
export function getVSCodeMcpServerUrlWithFallback(defaultUrl: string): string {
    return getVSCodeMcpServerUrl() || defaultUrl;
}
