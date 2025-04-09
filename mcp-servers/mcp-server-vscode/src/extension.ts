import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import dedent from 'dedent';
import express, { Request, Response } from 'express';
import * as http from 'http';
import * as vscode from 'vscode';
import { DiagnosticSeverity } from 'vscode';
import { z } from 'zod';
import packageJson from '../package.json';
import { codeCheckerTool } from './tools/code_checker';
import {
    getCallStack,
    getCallStackSchema,
    getStackFrameVariables,
    getStackFrameVariablesSchema,
    listDebugSessions,
    listDebugSessionsSchema,
    resumeDebugSession,
    resumeDebugSessionSchema,
    setBreakpoint,
    setBreakpointSchema,
    startDebugSession,
    startDebugSessionSchema,
    stopDebugSession,
    stopDebugSessionSchema,
} from './tools/debug_tools';
import { focusEditorTool } from './tools/focus_editor';
import { resolvePort } from './utils/port';

const extensionName = 'vscode-mcp-server';
const extensionDisplayName = 'VSCode MCP Server';

export const activate = async (context: vscode.ExtensionContext) => {
    // Create the output channel for logging
    const outputChannel = vscode.window.createOutputChannel(extensionDisplayName);

    // Write an initial message to ensure the channel appears in the Output dropdown
    outputChannel.appendLine(`Activating ${extensionDisplayName}...`);
    // Uncomment to automatically switch to the output tab and this extension channel on activation
    // outputChannel.show();

    // Initialize the MCP server instance
    const mcpServer = new McpServer({
        name: extensionName,
        version: packageJson.version,
    });

    // Register the "code_checker" tool.
    // This tool retrieves diagnostics from VSCode's language services,
    // filtering out files without issues.
    mcpServer.tool(
        'code_checker',
        dedent`
            Retrieve diagnostics from VSCode's language services for the active workspace.
            Use this tool after making changes to any code in the filesystem to ensure no new
            errors were introduced, or when requested by the user.
        `.trim(),
        // Passing the raw shape object directly
        {
            severityLevel: z
                .enum(['Error', 'Warning', 'Information', 'Hint'])
                .default('Warning')
                .describe("Minimum severity level for checking issues: 'Error', 'Warning', 'Information', or 'Hint'."),
        },
        async (params: { severityLevel?: 'Error' | 'Warning' | 'Information' | 'Hint' }) => {
            const severityLevel = params.severityLevel
                ? DiagnosticSeverity[params.severityLevel]
                : DiagnosticSeverity.Warning;
            const result = await codeCheckerTool(severityLevel);
            return {
                ...result,
                content: result.content.map((c) => ({
                    ...c,
                    text: typeof c.text === 'string' ? c.text : String(c.text),
                    type: 'text',
                })),
            };
        },
    );

    // Register 'focus_editor' tool
    mcpServer.tool(
        'focus_editor',
        dedent`
        Open the specified file in the VSCode editor and navigate to a specific line and column.
        Use this tool to bring a file into focus and position the editor's cursor where desired.
        Note: This tool operates on the editor visual environment so that the user can see the file. It does not return the file contents in the tool call result.
        `.trim(),
        {
            filePath: z.string().describe('The absolute path to the file to focus in the editor.'),
            line: z.number().int().min(0).default(0).describe('The line number to navigate to (default: 0).'),
            column: z.number().int().min(0).default(0).describe('The column position to navigate to (default: 0).'),
            startLine: z.number().int().min(0).optional().describe('The starting line number for highlighting.'),
            startColumn: z.number().int().min(0).optional().describe('The starting column number for highlighting.'),
            endLine: z.number().int().min(0).optional().describe('The ending line number for highlighting.'),
            endColumn: z.number().int().min(0).optional().describe('The ending column number for highlighting.'),
        },
        async (params: { filePath: string; line?: number; column?: number }) => {
            const result = await focusEditorTool(params);
            return result;
        },
    );

    // FIXME: This doesn't return results yet
    // // Register 'search_symbol' tool
    // mcpServer.tool(
    //     'search_symbol',
    //     dedent`
    //     Search for a symbol within the workspace.
    //     - Tries to resolve the definition via VSCode’s "Go to Definition".
    //     - If not found, searches the entire workspace for the text, similar to Ctrl+Shift+F.
    //     `.trim(),
    //     {
    //         query: z.string().describe('The symbol or text to search for.'),
    //         useDefinition: z.boolean().default(true).describe("Whether to use 'Go to Definition' as the first method."),
    //         maxResults: z.number().default(50).describe('Maximum number of global search results to return.'),
    //         openFile: z.boolean().default(false).describe('Whether to open the found file in the editor.'),
    //     },
    //     async (params: { query: string; useDefinition?: boolean; maxResults?: number; openFile?: boolean }) => {
    //         const result = await searchSymbolTool(params);
    //         return {
    //             ...result,
    //             content: [
    //                 {
    //                     text: JSON.stringify(result),
    //                     type: 'text',
    //                 },
    //             ],
    //         };
    //     },
    // );

    // Register 'list_debug_sessions' tool
    mcpServer.tool(
        'list_debug_sessions',
        'List all active debug sessions in the workspace.',
        listDebugSessionsSchema.shape, // No parameters required
        async () => {
            const result = await listDebugSessions();
            return {
                ...result,
                content: result.content.map((item) => ({ type: 'text', text: JSON.stringify(item.json) })),
            };
        },
    );

    // Register 'start_debug_session' tool
    mcpServer.tool(
        'start_debug_session',
        'Start a new debug session with the provided configuration.',
        startDebugSessionSchema.shape,
        async (params) => {
            const result = await startDebugSession(params);
            return {
                ...result,
                content: result.content.map((item) => ({
                    ...item,
                    type: 'text' as const,
                })),
            };
        },
    );

    // Register 'set_breakpoint' tool
    mcpServer.tool(
        'set_breakpoint',
        'Set a breakpoint at a specific line in a file.',
        setBreakpointSchema.shape,
        async (params) => {
            const result = await setBreakpoint(params);
            return {
                ...result,
                content: result.content.map((item) => ({
                    ...item,
                    type: 'text' as const,
                })),
            };
        },
    );

    // Register 'get_call_stack' tool
    mcpServer.tool(
        'get_call_stack',
        'Get the current call stack information for an active debug session.',
        getCallStackSchema.shape,
        async (params) => {
            const result = await getCallStack(params);
            return {
                ...result,
                content: result.content.map((item) => {
                    if ('json' in item) {
                        // Convert json content to text string
                        return { type: 'text' as const, text: JSON.stringify(item.json) };
                    }
                    return { ...item, type: 'text' as const };
                }),
            };
        },
    );

    // Register 'resume_debug_session' tool
    mcpServer.tool(
        'resume_debug_session',
        'Resume execution of a debug session that has been paused (e.g., by a breakpoint).',
        resumeDebugSessionSchema.shape,
        async (params) => {
            const result = await resumeDebugSession(params);
            return {
                ...result,
                content: result.content.map((item) => ({
                    ...item,
                    type: 'text' as const,
                })),
            };
        },
    );

    // Register 'get_stack_frame_variables' tool
    mcpServer.tool(
        'get_stack_frame_variables',
        'Get variables from a specific stack frame in a debug session.',
        getStackFrameVariablesSchema.shape,
        async (params) => {
            const result = await getStackFrameVariables(params);
            return {
                ...result,
                content: result.content.map((item) => {
                    if ('json' in item) {
                        // Convert json content to text string
                        return { type: 'text' as const, text: JSON.stringify(item.json) };
                    }
                    return { ...item, type: 'text' as const };
                }),
            };
        },
    );

    // Register 'stop_debug_session' tool
    mcpServer.tool(
        'stop_debug_session',
        'Stop all debug sessions that match the provided session name.',
        stopDebugSessionSchema.shape,
        async (params) => {
            const result = await stopDebugSession(params);
            return {
                ...result,
                content: result.content.map((item) => ({
                    ...item,
                    type: 'text' as const,
                })),
            };
        },
    );

    // Register 'restart_debug_session' tool
    mcpServer.tool(
        'restart_debug_session',
        'Restart a debug session by stopping it and then starting it with the provided configuration.',
        startDebugSessionSchema.shape, // using the same schema as 'start_debug_session'
        async (params) => {
            // Stop current session using the provided session name
            await stopDebugSession({ sessionName: params.configuration.name });

            // Then start a new debug session with the given configuration
            const result = await startDebugSession(params);
            return {
                ...result,
                content: result.content.map((item) => ({
                    ...item,
                    type: 'text' as const,
                })),
            };
        },
    );

    // Set up an Express app to handle SSE connections
    const app = express();
    const mcpConfig = vscode.workspace.getConfiguration('mcpServer');
    const port = await resolvePort(mcpConfig.get<number>('port', 6010));

    let sseTransport: SSEServerTransport | undefined;

    // GET /sse endpoint: the external MCP client connects here (SSE)
    app.get('/sse', async (_req: Request, res: Response) => {
        outputChannel.appendLine('SSE connection initiated...');
        sseTransport = new SSEServerTransport('/messages', res);
        try {
            await mcpServer.connect(sseTransport);
            outputChannel.appendLine('MCP Server connected via SSE.');
            outputChannel.appendLine(`SSE Transport sessionId: ${sseTransport.sessionId}`);
        } catch (err) {
            outputChannel.appendLine('Error connecting MCP Server via SSE: ' + err);
        }
    });

    // POST /messages endpoint: the external MCP client sends messages here
    app.post('/messages', express.json(), async (req: Request, res: Response) => {
        // Log in output channel
        outputChannel.appendLine(`POST /messages: Payload - ${JSON.stringify(req.body, null, 2)}`);

        if (sseTransport) {
            // Log the session ID of the transport to confirm its initialization
            outputChannel.appendLine(`SSE Transport sessionId: ${sseTransport.sessionId}`);
            try {
                // Note: Passing req.body to handlePostMessage is critical because express.json()
                // consumes the request stream. Without this, attempting to re-read the stream
                // within handlePostMessage would result in a "stream is not readable" error.
                await sseTransport.handlePostMessage(req, res, req.body);
                outputChannel.appendLine('Handled POST /messages successfully.');
            } catch (err) {
                outputChannel.appendLine('Error handling POST /messages: ' + err);
            }
        } else {
            res.status(500).send('SSE Transport not initialized.');
            outputChannel.appendLine('POST /messages failed: SSE Transport not initialized.');
        }
    });

    // Create and start the HTTP server
    const server = http.createServer(app);
    function startServer(port: number): void {
        server.listen(port, () => {
            outputChannel.appendLine(`MCP SSE Server running at http://127.0.0.1:${port}/sse`);
        });

        // Add disposal to shut down the HTTP server and output channel on extension deactivation
        context.subscriptions.push({
            dispose: () => {
                server.close();
                outputChannel.dispose();
            },
        });
    }
    const startOnActivate = mcpConfig.get<boolean>('startOnActivate', true);
    if (startOnActivate) {
        startServer(port);
    } else {
        outputChannel.appendLine('MCP Server startup disabled by configuration.');
    }

    // COMMAND PALETTE COMMAND: Stop the MCP Server
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpServer.stopServer', () => {
            if (!server.listening) {
                vscode.window.showWarningMessage('MCP Server is not running.');
                outputChannel.appendLine('Attempted to stop the MCP Server, but it is not running.');
                return;
            }
            server.close(() => {
                outputChannel.appendLine('MCP Server stopped.');
                vscode.window.showInformationMessage('MCP Server stopped.');
            });
        }),
    );

    // COMMAND PALETTE COMMAND: Start the MCP Server
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpServer.startServer', async () => {
            if (server.listening) {
                vscode.window.showWarningMessage('MCP Server is already running.');
                outputChannel.appendLine('Attempted to start the MCP Server, but it is already running.');
                return;
            }
            const newPort = await resolvePort(mcpConfig.get<number>('port', 6010));
            startServer(newPort);
            outputChannel.appendLine(`MCP Server started on port ${newPort}.`);
            vscode.window.showInformationMessage(`MCP Server started on port ${newPort}.`);
        }),
    );

    // COMMAND PALETTE COMMAND: Set the MCP server port and restart the server
    context.subscriptions.push(
        vscode.commands.registerCommand('mcpServer.setPort', async () => {
            const newPortInput = await vscode.window.showInputBox({
                prompt: 'Enter new port number for the MCP Server:',
                value: String(port),
                validateInput: (input) => {
                    const num = Number(input);
                    if (isNaN(num) || num < 1 || num > 65535) {
                        return 'Please enter a valid port number (1-65535).';
                    }
                    return null;
                },
            });
            if (newPortInput && newPortInput.trim().length > 0) {
                const newPort = Number(newPortInput);
                // Update the configuration so that subsequent startups use the new port
                await vscode.workspace
                    .getConfiguration('mcpServer')
                    .update('port', newPort, vscode.ConfigurationTarget.Global);
                // Restart the server: close existing server and start a new one
                server.close();
                startServer(newPort);
                outputChannel.appendLine(`MCP Server restarted on port ${newPort}`);
                vscode.window.showInformationMessage(`MCP Server restarted on port ${newPort}`);
            }
        }),
    );

    outputChannel.appendLine(`${extensionDisplayName} activated.`);
};

export function deactivate() {
    // Clean-up is managed by the disposables added in the activate method.
}
