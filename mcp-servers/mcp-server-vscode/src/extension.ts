import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createServer } from 'http';
import * as vscode from 'vscode';

// Global variable for the MCP server instance
let mcpServer: Server;

// The port the SSE server will run on - dynamically allocated
let serverPort: number = 0;

export function activate(context: vscode.ExtensionContext) {
    const disposable = vscode.commands.registerCommand('mcp-server-vscode.startServer', async () => {
        await startMCPServer();
    });

    context.subscriptions.push(disposable);

    // Auto-start the server on extension activation
    startMCPServer();
}

/**
 * Start the MCP server with both stdio and SSE transports
 */
async function startMCPServer() {
    const outputChannel = vscode.window.createOutputChannel('VSCode MCP Server');
    outputChannel.show();
    outputChannel.appendLine('Starting VSCode MCP Server...');

    // Create the MCP server
    mcpServer = new Server(
        {
            name: 'vscode',
            version: '0.1.0',
        },
        {
            capabilities: {
                tools: {},
            },
        },
    );

    // Register handlers (commented out for now - will be implemented in a separate PR)
    // registerHandlers(mcpServer);

    // Handle server errors
    mcpServer.onerror = (error) => {
        outputChannel.appendLine(`[MCP Error] ${error}`);
    };

    try {
        // Start the stdio transport for internal communication
        const stdioTransport = new StdioServerTransport();
        await mcpServer.connect(stdioTransport);
        outputChannel.appendLine('VSCode MCP server started on stdio transport');

        // Start the SSE transport for external communication
        const ssePort = await startSseServer(outputChannel);
        serverPort = ssePort;

        // Notify workbench of the MCP server URL
        updateWorkbenchMcpServerUrl(ssePort);

        outputChannel.appendLine(`VSCode MCP server started on SSE transport - http://127.0.0.1:${ssePort}/sse`);
    } catch (error) {
        outputChannel.appendLine(`Error starting MCP server: ${error}`);
    }
}

/**
 * Start the SSE server on a dynamic port
 */
async function startSseServer(outputChannel: vscode.OutputChannel): Promise<number> {
    return new Promise((resolve, reject) => {
        // Create an HTTP server
        const httpServer = createServer();

        // Start on port 0 to let the OS assign an available port
        httpServer.listen(0, '127.0.0.1', () => {
            const addressInfo = httpServer.address() as { port: number };
            const port = addressInfo.port;

            // Create the SSE transport using the HTTP server
            const sseTransport = new SSEServerTransport({ path: '/sse', server: httpServer });

            // Connect the MCP server to the SSE transport
            mcpServer.connect(sseTransport).catch(reject);

            // Resolve with the dynamically assigned port
            resolve(port);
        });

        httpServer.on('error', (error) => {
            outputChannel.appendLine(`Error starting SSE server: ${error}`);
            reject(error);
        });
    });
}

/**
 * Update the workbench with the MCP server URL
 */
async function updateWorkbenchMcpServerUrl(port: number) {
    try {
        // Run the update script to notify the workbench of the server URL
        const updateCommand = `node ${
            vscode.Uri.joinPath(
                vscode.Uri.file(__dirname),
                '..',
                '..',
                '..',
                '..',
                'scripts',
                'update-vscode-mcp-url.js',
            ).fsPath
        } http://127.0.0.1:${port}/sse`;

        // Execute the command
        const cp = require('child_process');
        cp.exec(updateCommand, (error: any, stdout: any, stderr: any) => {
            if (error) {
                console.error(`Error updating workbench MCP server URL: ${error}`);
                return;
            }
            console.log(`Workbench MCP server URL updated to http://127.0.0.1:${port}/sse`);
        });
    } catch (error) {
        console.error(`Error running update script: ${error}`);
    }
}

/**
 * Clean up resources when the extension is deactivated
 */
export function deactivate() {
    if (mcpServer) {
        // If the server was running, reset the workbench MCP server URL
        if (serverPort > 0) {
            try {
                const cp = require('child_process');
                const resetCommand = `node ${
                    vscode.Uri.joinPath(
                        vscode.Uri.file(__dirname),
                        '..',
                        '..',
                        '..',
                        '..',
                        'scripts',
                        'update-vscode-mcp-url.js',
                    ).fsPath
                } reset`;
                cp.exec(resetCommand);
            } catch (error) {
                console.error(`Error resetting workbench MCP server URL: ${error}`);
            }
        }

        // Close the MCP server
        mcpServer.close().catch(console.error);
    }
}
