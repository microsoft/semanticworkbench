import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { SSEServerTransport } from '@modelcontextprotocol/sdk/server/sse.js';
import dedent from 'dedent';
import express from 'express';
import * as http from 'http';
import * as vscode from 'vscode';
import { DiagnosticSeverity } from 'vscode';
import { z } from 'zod';
import packageJson from '../package.json';
import { codeCheckerTool } from './tools/code_checker';
import { listDebugSessions, listDebugSessionsSchema, startDebugSession, startDebugSessionSchema, stopDebugSession, stopDebugSessionSchema, } from './tools/debug_tools';
import { focusEditorTool } from './tools/focus_editor';
import { resolvePort } from './utils/port';
const extensionName = 'vscode-mcp-server';
const extensionDisplayName = 'VSCode MCP Server';
export const activate = async (context) => {
    const outputChannel = vscode.window.createOutputChannel(extensionDisplayName);
    outputChannel.appendLine(`Activating ${extensionDisplayName}...`);
    const mcpServer = new McpServer({
        name: extensionName,
        version: packageJson.version,
    });
    mcpServer.tool('code_checker', dedent `
            Retrieve diagnostics from VSCode's language services for the active workspace.
            Use this tool after making changes to any code in the filesystem to ensure no new
            errors were introduced, or when requested by the user.
        `.trim(), {
        severityLevel: z
            .enum(['Error', 'Warning', 'Information', 'Hint'])
            .default('Warning')
            .describe("Minimum severity level for checking issues: 'Error', 'Warning', 'Information', or 'Hint'."),
    }, async (params) => {
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
    });
    mcpServer.tool('focus_editor', dedent `
        Open the specified file in the VSCode editor and navigate to a specific line and column.
        Use this tool to bring a file into focus and position the editor's cursor where desired.
        Note: This tool operates on the editor visual environment so that the user can see the file. It does not return the file contents in the tool call result.
        `.trim(), {
        filePath: z.string().describe('The absolute path to the file to focus in the editor.'),
        line: z.number().int().min(0).default(0).describe('The line number to navigate to (default: 0).'),
        column: z.number().int().min(0).default(0).describe('The column position to navigate to (default: 0).'),
        startLine: z.number().int().min(0).optional().describe('The starting line number for highlighting.'),
        startColumn: z.number().int().min(0).optional().describe('The starting column number for highlighting.'),
        endLine: z.number().int().min(0).optional().describe('The ending line number for highlighting.'),
        endColumn: z.number().int().min(0).optional().describe('The ending column number for highlighting.'),
    }, async (params) => {
        const result = await focusEditorTool(params);
        return result;
    });
    mcpServer.tool('list_debug_sessions', 'List all active debug sessions in the workspace.', listDebugSessionsSchema.shape, async () => {
        const result = await listDebugSessions();
        return {
            ...result,
            content: result.content.map((item) => ({ type: 'text', text: JSON.stringify(item.json) })),
        };
    });
    mcpServer.tool('start_debug_session', 'Start a new debug session with the provided configuration.', startDebugSessionSchema.shape, async (params) => {
        const result = await startDebugSession(params);
        return {
            ...result,
            content: result.content.map((item) => ({
                ...item,
                type: 'text',
            })),
        };
    });
    mcpServer.tool('restart_debug_session', 'Restart a debug session by stopping it and then starting it with the provided configuration.', startDebugSessionSchema.shape, async (params) => {
        await stopDebugSession({ sessionName: params.configuration.name });
        const result = await startDebugSession(params);
        return {
            ...result,
            content: result.content.map((item) => ({
                ...item,
                type: 'text',
            })),
        };
    });
    mcpServer.tool('stop_debug_session', 'Stop all debug sessions that match the provided session name.', stopDebugSessionSchema.shape, async (params) => {
        const result = await stopDebugSession(params);
        return {
            ...result,
            content: result.content.map((item) => ({
                ...item,
                type: 'text',
            })),
        };
    });
    const app = express();
    const mcpConfig = vscode.workspace.getConfiguration('mcpServer');
    const port = await resolvePort(mcpConfig.get('port', 6010));
    let sseTransport;
    app.get('/sse', async (_req, res) => {
        outputChannel.appendLine('SSE connection initiated...');
        sseTransport = new SSEServerTransport('/messages', res);
        try {
            await mcpServer.connect(sseTransport);
            outputChannel.appendLine('MCP Server connected via SSE.');
            outputChannel.appendLine(`SSE Transport sessionId: ${sseTransport.sessionId}`);
        }
        catch (err) {
            outputChannel.appendLine('Error connecting MCP Server via SSE: ' + err);
        }
    });
    app.post('/messages', express.json(), async (req, res) => {
        outputChannel.appendLine(`POST /messages: Payload - ${JSON.stringify(req.body, null, 2)}`);
        if (sseTransport) {
            outputChannel.appendLine(`SSE Transport sessionId: ${sseTransport.sessionId}`);
            try {
                await sseTransport.handlePostMessage(req, res, req.body);
                outputChannel.appendLine('Handled POST /messages successfully.');
            }
            catch (err) {
                outputChannel.appendLine('Error handling POST /messages: ' + err);
            }
        }
        else {
            res.status(500).send('SSE Transport not initialized.');
            outputChannel.appendLine('POST /messages failed: SSE Transport not initialized.');
        }
    });
    const server = http.createServer(app);
    function startServer(port) {
        server.listen(port, () => {
            outputChannel.appendLine(`MCP SSE Server running at http://127.0.0.1:${port}/sse`);
        });
        context.subscriptions.push({
            dispose: () => {
                server.close();
                outputChannel.dispose();
            },
        });
    }
    const startOnActivate = mcpConfig.get('startOnActivate', true);
    if (startOnActivate) {
        startServer(port);
    }
    else {
        outputChannel.appendLine('MCP Server startup disabled by configuration.');
    }
    context.subscriptions.push(vscode.commands.registerCommand('mcpServer.stopServer', () => {
        if (!server.listening) {
            vscode.window.showWarningMessage('MCP Server is not running.');
            outputChannel.appendLine('Attempted to stop the MCP Server, but it is not running.');
            return;
        }
        server.close(() => {
            outputChannel.appendLine('MCP Server stopped.');
            vscode.window.showInformationMessage('MCP Server stopped.');
        });
    }));
    context.subscriptions.push(vscode.commands.registerCommand('mcpServer.startServer', async () => {
        if (server.listening) {
            vscode.window.showWarningMessage('MCP Server is already running.');
            outputChannel.appendLine('Attempted to start the MCP Server, but it is already running.');
            return;
        }
        const newPort = await resolvePort(mcpConfig.get('port', 6010));
        startServer(newPort);
        outputChannel.appendLine(`MCP Server started on port ${newPort}.`);
        vscode.window.showInformationMessage(`MCP Server started on port ${newPort}.`);
    }));
    context.subscriptions.push(vscode.commands.registerCommand('mcpServer.setPort', async () => {
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
            await vscode.workspace
                .getConfiguration('mcpServer')
                .update('port', newPort, vscode.ConfigurationTarget.Global);
            server.close();
            startServer(newPort);
            outputChannel.appendLine(`MCP Server restarted on port ${newPort}`);
            vscode.window.showInformationMessage(`MCP Server restarted on port ${newPort}`);
        }
    }));
    outputChannel.appendLine(`${extensionDisplayName} activated.`);
};
export function deactivate() {
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZXh0ZW5zaW9uLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXMiOlsiLi4vc3JjL2V4dGVuc2lvbi50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxPQUFPLEVBQUUsU0FBUyxFQUFFLE1BQU0seUNBQXlDLENBQUM7QUFDcEUsT0FBTyxFQUFFLGtCQUFrQixFQUFFLE1BQU0seUNBQXlDLENBQUM7QUFDN0UsT0FBTyxNQUFNLE1BQU0sUUFBUSxDQUFDO0FBQzVCLE9BQU8sT0FBOEIsTUFBTSxTQUFTLENBQUM7QUFDckQsT0FBTyxLQUFLLElBQUksTUFBTSxNQUFNLENBQUM7QUFDN0IsT0FBTyxLQUFLLE1BQU0sTUFBTSxRQUFRLENBQUM7QUFDakMsT0FBTyxFQUFFLGtCQUFrQixFQUFFLE1BQU0sUUFBUSxDQUFDO0FBQzVDLE9BQU8sRUFBRSxDQUFDLEVBQUUsTUFBTSxLQUFLLENBQUM7QUFDeEIsT0FBTyxXQUFXLE1BQU0saUJBQWlCLENBQUM7QUFDMUMsT0FBTyxFQUFFLGVBQWUsRUFBRSxNQUFNLHNCQUFzQixDQUFDO0FBQ3ZELE9BQU8sRUFDSCxpQkFBaUIsRUFDakIsdUJBQXVCLEVBQ3ZCLGlCQUFpQixFQUNqQix1QkFBdUIsRUFDdkIsZ0JBQWdCLEVBQ2hCLHNCQUFzQixHQUN6QixNQUFNLHFCQUFxQixDQUFDO0FBQzdCLE9BQU8sRUFBRSxlQUFlLEVBQUUsTUFBTSxzQkFBc0IsQ0FBQztBQUN2RCxPQUFPLEVBQUUsV0FBVyxFQUFFLE1BQU0sY0FBYyxDQUFDO0FBRTNDLE1BQU0sYUFBYSxHQUFHLG1CQUFtQixDQUFDO0FBQzFDLE1BQU0sb0JBQW9CLEdBQUcsbUJBQW1CLENBQUM7QUFFakQsTUFBTSxDQUFDLE1BQU0sUUFBUSxHQUFHLEtBQUssRUFBRSxPQUFnQyxFQUFFLEVBQUU7SUFFL0QsTUFBTSxhQUFhLEdBQUcsTUFBTSxDQUFDLE1BQU0sQ0FBQyxtQkFBbUIsQ0FBQyxvQkFBb0IsQ0FBQyxDQUFDO0lBRzlFLGFBQWEsQ0FBQyxVQUFVLENBQUMsY0FBYyxvQkFBb0IsS0FBSyxDQUFDLENBQUM7SUFLbEUsTUFBTSxTQUFTLEdBQUcsSUFBSSxTQUFTLENBQUM7UUFDNUIsSUFBSSxFQUFFLGFBQWE7UUFDbkIsT0FBTyxFQUFFLFdBQVcsQ0FBQyxPQUFPO0tBQy9CLENBQUMsQ0FBQztJQUtILFNBQVMsQ0FBQyxJQUFJLENBQ1YsY0FBYyxFQUNkLE1BQU0sQ0FBQTs7OztTQUlMLENBQUMsSUFBSSxFQUFFLEVBRVI7UUFDSSxhQUFhLEVBQUUsQ0FBQzthQUNYLElBQUksQ0FBQyxDQUFDLE9BQU8sRUFBRSxTQUFTLEVBQUUsYUFBYSxFQUFFLE1BQU0sQ0FBQyxDQUFDO2FBQ2pELE9BQU8sQ0FBQyxTQUFTLENBQUM7YUFDbEIsUUFBUSxDQUFDLDJGQUEyRixDQUFDO0tBQzdHLEVBQ0QsS0FBSyxFQUFFLE1BQXdFLEVBQUUsRUFBRTtRQUMvRSxNQUFNLGFBQWEsR0FBRyxNQUFNLENBQUMsYUFBYTtZQUN0QyxDQUFDLENBQUMsa0JBQWtCLENBQUMsTUFBTSxDQUFDLGFBQWEsQ0FBQztZQUMxQyxDQUFDLENBQUMsa0JBQWtCLENBQUMsT0FBTyxDQUFDO1FBQ2pDLE1BQU0sTUFBTSxHQUFHLE1BQU0sZUFBZSxDQUFDLGFBQWEsQ0FBQyxDQUFDO1FBQ3BELE9BQU87WUFDSCxHQUFHLE1BQU07WUFDVCxPQUFPLEVBQUUsTUFBTSxDQUFDLE9BQU8sQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLEVBQUUsRUFBRSxDQUFDLENBQUM7Z0JBQ2hDLEdBQUcsQ0FBQztnQkFDSixJQUFJLEVBQUUsT0FBTyxDQUFDLENBQUMsSUFBSSxLQUFLLFFBQVEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLElBQUksQ0FBQyxDQUFDLENBQUMsTUFBTSxDQUFDLENBQUMsQ0FBQyxJQUFJLENBQUM7Z0JBQzFELElBQUksRUFBRSxNQUFNO2FBQ2YsQ0FBQyxDQUFDO1NBQ04sQ0FBQztJQUNOLENBQUMsQ0FDSixDQUFDO0lBR0YsU0FBUyxDQUFDLElBQUksQ0FDVixjQUFjLEVBQ2QsTUFBTSxDQUFBOzs7O1NBSUwsQ0FBQyxJQUFJLEVBQUUsRUFDUjtRQUNJLFFBQVEsRUFBRSxDQUFDLENBQUMsTUFBTSxFQUFFLENBQUMsUUFBUSxDQUFDLHVEQUF1RCxDQUFDO1FBQ3RGLElBQUksRUFBRSxDQUFDLENBQUMsTUFBTSxFQUFFLENBQUMsR0FBRyxFQUFFLENBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxDQUFDLE9BQU8sQ0FBQyxDQUFDLENBQUMsQ0FBQyxRQUFRLENBQUMsOENBQThDLENBQUM7UUFDakcsTUFBTSxFQUFFLENBQUMsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxHQUFHLEVBQUUsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsT0FBTyxDQUFDLENBQUMsQ0FBQyxDQUFDLFFBQVEsQ0FBQyxrREFBa0QsQ0FBQztRQUN2RyxTQUFTLEVBQUUsQ0FBQyxDQUFDLE1BQU0sRUFBRSxDQUFDLEdBQUcsRUFBRSxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxRQUFRLEVBQUUsQ0FBQyxRQUFRLENBQUMsNENBQTRDLENBQUM7UUFDcEcsV0FBVyxFQUFFLENBQUMsQ0FBQyxNQUFNLEVBQUUsQ0FBQyxHQUFHLEVBQUUsQ0FBQyxHQUFHLENBQUMsQ0FBQyxDQUFDLENBQUMsUUFBUSxFQUFFLENBQUMsUUFBUSxDQUFDLDhDQUE4QyxDQUFDO1FBQ3hHLE9BQU8sRUFBRSxDQUFDLENBQUMsTUFBTSxFQUFFLENBQUMsR0FBRyxFQUFFLENBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxDQUFDLFFBQVEsRUFBRSxDQUFDLFFBQVEsQ0FBQywwQ0FBMEMsQ0FBQztRQUNoRyxTQUFTLEVBQUUsQ0FBQyxDQUFDLE1BQU0sRUFBRSxDQUFDLEdBQUcsRUFBRSxDQUFDLEdBQUcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxRQUFRLEVBQUUsQ0FBQyxRQUFRLENBQUMsNENBQTRDLENBQUM7S0FDdkcsRUFDRCxLQUFLLEVBQUUsTUFBNEQsRUFBRSxFQUFFO1FBQ25FLE1BQU0sTUFBTSxHQUFHLE1BQU0sZUFBZSxDQUFDLE1BQU0sQ0FBQyxDQUFDO1FBQzdDLE9BQU8sTUFBTSxDQUFDO0lBQ2xCLENBQUMsQ0FDSixDQUFDO0lBZ0NGLFNBQVMsQ0FBQyxJQUFJLENBQ1YscUJBQXFCLEVBQ3JCLGtEQUFrRCxFQUNsRCx1QkFBdUIsQ0FBQyxLQUFLLEVBQzdCLEtBQUssSUFBSSxFQUFFO1FBQ1AsTUFBTSxNQUFNLEdBQUcsTUFBTSxpQkFBaUIsRUFBRSxDQUFDO1FBQ3pDLE9BQU87WUFDSCxHQUFHLE1BQU07WUFDVCxPQUFPLEVBQUUsTUFBTSxDQUFDLE9BQU8sQ0FBQyxHQUFHLENBQUMsQ0FBQyxJQUFJLEVBQUUsRUFBRSxDQUFDLENBQUMsRUFBRSxJQUFJLEVBQUUsTUFBTSxFQUFFLElBQUksRUFBRSxJQUFJLENBQUMsU0FBUyxDQUFDLElBQUksQ0FBQyxJQUFJLENBQUMsRUFBRSxDQUFDLENBQUM7U0FDN0YsQ0FBQztJQUNOLENBQUMsQ0FDSixDQUFDO0lBR0YsU0FBUyxDQUFDLElBQUksQ0FDVixxQkFBcUIsRUFDckIsNERBQTRELEVBQzVELHVCQUF1QixDQUFDLEtBQUssRUFDN0IsS0FBSyxFQUFFLE1BQU0sRUFBRSxFQUFFO1FBQ2IsTUFBTSxNQUFNLEdBQUcsTUFBTSxpQkFBaUIsQ0FBQyxNQUFNLENBQUMsQ0FBQztRQUMvQyxPQUFPO1lBQ0gsR0FBRyxNQUFNO1lBQ1QsT0FBTyxFQUFFLE1BQU0sQ0FBQyxPQUFPLENBQUMsR0FBRyxDQUFDLENBQUMsSUFBSSxFQUFFLEVBQUUsQ0FBQyxDQUFDO2dCQUNuQyxHQUFHLElBQUk7Z0JBQ1AsSUFBSSxFQUFFLE1BQWU7YUFDeEIsQ0FBQyxDQUFDO1NBQ04sQ0FBQztJQUNOLENBQUMsQ0FDSixDQUFDO0lBS0YsU0FBUyxDQUFDLElBQUksQ0FDVix1QkFBdUIsRUFDdkIsOEZBQThGLEVBQzlGLHVCQUF1QixDQUFDLEtBQUssRUFDN0IsS0FBSyxFQUFFLE1BQU0sRUFBRSxFQUFFO1FBRWIsTUFBTSxnQkFBZ0IsQ0FBQyxFQUFFLFdBQVcsRUFBRSxNQUFNLENBQUMsYUFBYSxDQUFDLElBQUksRUFBRSxDQUFDLENBQUM7UUFHbkUsTUFBTSxNQUFNLEdBQUcsTUFBTSxpQkFBaUIsQ0FBQyxNQUFNLENBQUMsQ0FBQztRQUMvQyxPQUFPO1lBQ0gsR0FBRyxNQUFNO1lBQ1QsT0FBTyxFQUFFLE1BQU0sQ0FBQyxPQUFPLENBQUMsR0FBRyxDQUFDLENBQUMsSUFBSSxFQUFFLEVBQUUsQ0FBQyxDQUFDO2dCQUNuQyxHQUFHLElBQUk7Z0JBQ1AsSUFBSSxFQUFFLE1BQWU7YUFDeEIsQ0FBQyxDQUFDO1NBQ04sQ0FBQztJQUNOLENBQUMsQ0FDSixDQUFDO0lBQ0YsU0FBUyxDQUFDLElBQUksQ0FDVixvQkFBb0IsRUFDcEIsK0RBQStELEVBQy9ELHNCQUFzQixDQUFDLEtBQUssRUFDNUIsS0FBSyxFQUFFLE1BQU0sRUFBRSxFQUFFO1FBQ2IsTUFBTSxNQUFNLEdBQUcsTUFBTSxnQkFBZ0IsQ0FBQyxNQUFNLENBQUMsQ0FBQztRQUM5QyxPQUFPO1lBQ0gsR0FBRyxNQUFNO1lBQ1QsT0FBTyxFQUFFLE1BQU0sQ0FBQyxPQUFPLENBQUMsR0FBRyxDQUFDLENBQUMsSUFBSSxFQUFFLEVBQUUsQ0FBQyxDQUFDO2dCQUNuQyxHQUFHLElBQUk7Z0JBQ1AsSUFBSSxFQUFFLE1BQWU7YUFDeEIsQ0FBQyxDQUFDO1NBQ04sQ0FBQztJQUNOLENBQUMsQ0FDSixDQUFDO0lBR0YsTUFBTSxHQUFHLEdBQUcsT0FBTyxFQUFFLENBQUM7SUFDdEIsTUFBTSxTQUFTLEdBQUcsTUFBTSxDQUFDLFNBQVMsQ0FBQyxnQkFBZ0IsQ0FBQyxXQUFXLENBQUMsQ0FBQztJQUNqRSxNQUFNLElBQUksR0FBRyxNQUFNLFdBQVcsQ0FBQyxTQUFTLENBQUMsR0FBRyxDQUFTLE1BQU0sRUFBRSxJQUFJLENBQUMsQ0FBQyxDQUFDO0lBRXBFLElBQUksWUFBNEMsQ0FBQztJQUdqRCxHQUFHLENBQUMsR0FBRyxDQUFDLE1BQU0sRUFBRSxLQUFLLEVBQUUsSUFBYSxFQUFFLEdBQWEsRUFBRSxFQUFFO1FBQ25ELGFBQWEsQ0FBQyxVQUFVLENBQUMsNkJBQTZCLENBQUMsQ0FBQztRQUN4RCxZQUFZLEdBQUcsSUFBSSxrQkFBa0IsQ0FBQyxXQUFXLEVBQUUsR0FBRyxDQUFDLENBQUM7UUFDeEQsSUFBSSxDQUFDO1lBQ0QsTUFBTSxTQUFTLENBQUMsT0FBTyxDQUFDLFlBQVksQ0FBQyxDQUFDO1lBQ3RDLGFBQWEsQ0FBQyxVQUFVLENBQUMsK0JBQStCLENBQUMsQ0FBQztZQUMxRCxhQUFhLENBQUMsVUFBVSxDQUFDLDRCQUE0QixZQUFZLENBQUMsU0FBUyxFQUFFLENBQUMsQ0FBQztRQUNuRixDQUFDO1FBQUMsT0FBTyxHQUFHLEVBQUUsQ0FBQztZQUNYLGFBQWEsQ0FBQyxVQUFVLENBQUMsdUNBQXVDLEdBQUcsR0FBRyxDQUFDLENBQUM7UUFDNUUsQ0FBQztJQUNMLENBQUMsQ0FBQyxDQUFDO0lBR0gsR0FBRyxDQUFDLElBQUksQ0FBQyxXQUFXLEVBQUUsT0FBTyxDQUFDLElBQUksRUFBRSxFQUFFLEtBQUssRUFBRSxHQUFZLEVBQUUsR0FBYSxFQUFFLEVBQUU7UUFFeEUsYUFBYSxDQUFDLFVBQVUsQ0FBQyw2QkFBNkIsSUFBSSxDQUFDLFNBQVMsQ0FBQyxHQUFHLENBQUMsSUFBSSxFQUFFLElBQUksRUFBRSxDQUFDLENBQUMsRUFBRSxDQUFDLENBQUM7UUFFM0YsSUFBSSxZQUFZLEVBQUUsQ0FBQztZQUVmLGFBQWEsQ0FBQyxVQUFVLENBQUMsNEJBQTRCLFlBQVksQ0FBQyxTQUFTLEVBQUUsQ0FBQyxDQUFDO1lBQy9FLElBQUksQ0FBQztnQkFJRCxNQUFNLFlBQVksQ0FBQyxpQkFBaUIsQ0FBQyxHQUFHLEVBQUUsR0FBRyxFQUFFLEdBQUcsQ0FBQyxJQUFJLENBQUMsQ0FBQztnQkFDekQsYUFBYSxDQUFDLFVBQVUsQ0FBQyxzQ0FBc0MsQ0FBQyxDQUFDO1lBQ3JFLENBQUM7WUFBQyxPQUFPLEdBQUcsRUFBRSxDQUFDO2dCQUNYLGFBQWEsQ0FBQyxVQUFVLENBQUMsaUNBQWlDLEdBQUcsR0FBRyxDQUFDLENBQUM7WUFDdEUsQ0FBQztRQUNMLENBQUM7YUFBTSxDQUFDO1lBQ0osR0FBRyxDQUFDLE1BQU0sQ0FBQyxHQUFHLENBQUMsQ0FBQyxJQUFJLENBQUMsZ0NBQWdDLENBQUMsQ0FBQztZQUN2RCxhQUFhLENBQUMsVUFBVSxDQUFDLHVEQUF1RCxDQUFDLENBQUM7UUFDdEYsQ0FBQztJQUNMLENBQUMsQ0FBQyxDQUFDO0lBR0gsTUFBTSxNQUFNLEdBQUcsSUFBSSxDQUFDLFlBQVksQ0FBQyxHQUFHLENBQUMsQ0FBQztJQUN0QyxTQUFTLFdBQVcsQ0FBQyxJQUFZO1FBQzdCLE1BQU0sQ0FBQyxNQUFNLENBQUMsSUFBSSxFQUFFLEdBQUcsRUFBRTtZQUNyQixhQUFhLENBQUMsVUFBVSxDQUFDLDhDQUE4QyxJQUFJLE1BQU0sQ0FBQyxDQUFDO1FBQ3ZGLENBQUMsQ0FBQyxDQUFDO1FBR0gsT0FBTyxDQUFDLGFBQWEsQ0FBQyxJQUFJLENBQUM7WUFDdkIsT0FBTyxFQUFFLEdBQUcsRUFBRTtnQkFDVixNQUFNLENBQUMsS0FBSyxFQUFFLENBQUM7Z0JBQ2YsYUFBYSxDQUFDLE9BQU8sRUFBRSxDQUFDO1lBQzVCLENBQUM7U0FDSixDQUFDLENBQUM7SUFDUCxDQUFDO0lBQ0QsTUFBTSxlQUFlLEdBQUcsU0FBUyxDQUFDLEdBQUcsQ0FBVSxpQkFBaUIsRUFBRSxJQUFJLENBQUMsQ0FBQztJQUN4RSxJQUFJLGVBQWUsRUFBRSxDQUFDO1FBQ2xCLFdBQVcsQ0FBQyxJQUFJLENBQUMsQ0FBQztJQUN0QixDQUFDO1NBQU0sQ0FBQztRQUNKLGFBQWEsQ0FBQyxVQUFVLENBQUMsK0NBQStDLENBQUMsQ0FBQztJQUM5RSxDQUFDO0lBR0QsT0FBTyxDQUFDLGFBQWEsQ0FBQyxJQUFJLENBQ3RCLE1BQU0sQ0FBQyxRQUFRLENBQUMsZUFBZSxDQUFDLHNCQUFzQixFQUFFLEdBQUcsRUFBRTtRQUN6RCxJQUFJLENBQUMsTUFBTSxDQUFDLFNBQVMsRUFBRSxDQUFDO1lBQ3BCLE1BQU0sQ0FBQyxNQUFNLENBQUMsa0JBQWtCLENBQUMsNEJBQTRCLENBQUMsQ0FBQztZQUMvRCxhQUFhLENBQUMsVUFBVSxDQUFDLDBEQUEwRCxDQUFDLENBQUM7WUFDckYsT0FBTztRQUNYLENBQUM7UUFDRCxNQUFNLENBQUMsS0FBSyxDQUFDLEdBQUcsRUFBRTtZQUNkLGFBQWEsQ0FBQyxVQUFVLENBQUMscUJBQXFCLENBQUMsQ0FBQztZQUNoRCxNQUFNLENBQUMsTUFBTSxDQUFDLHNCQUFzQixDQUFDLHFCQUFxQixDQUFDLENBQUM7UUFDaEUsQ0FBQyxDQUFDLENBQUM7SUFDUCxDQUFDLENBQUMsQ0FDTCxDQUFDO0lBR0YsT0FBTyxDQUFDLGFBQWEsQ0FBQyxJQUFJLENBQ3RCLE1BQU0sQ0FBQyxRQUFRLENBQUMsZUFBZSxDQUFDLHVCQUF1QixFQUFFLEtBQUssSUFBSSxFQUFFO1FBQ2hFLElBQUksTUFBTSxDQUFDLFNBQVMsRUFBRSxDQUFDO1lBQ25CLE1BQU0sQ0FBQyxNQUFNLENBQUMsa0JBQWtCLENBQUMsZ0NBQWdDLENBQUMsQ0FBQztZQUNuRSxhQUFhLENBQUMsVUFBVSxDQUFDLCtEQUErRCxDQUFDLENBQUM7WUFDMUYsT0FBTztRQUNYLENBQUM7UUFDRCxNQUFNLE9BQU8sR0FBRyxNQUFNLFdBQVcsQ0FBQyxTQUFTLENBQUMsR0FBRyxDQUFTLE1BQU0sRUFBRSxJQUFJLENBQUMsQ0FBQyxDQUFDO1FBQ3ZFLFdBQVcsQ0FBQyxPQUFPLENBQUMsQ0FBQztRQUNyQixhQUFhLENBQUMsVUFBVSxDQUFDLDhCQUE4QixPQUFPLEdBQUcsQ0FBQyxDQUFDO1FBQ25FLE1BQU0sQ0FBQyxNQUFNLENBQUMsc0JBQXNCLENBQUMsOEJBQThCLE9BQU8sR0FBRyxDQUFDLENBQUM7SUFDbkYsQ0FBQyxDQUFDLENBQ0wsQ0FBQztJQUdGLE9BQU8sQ0FBQyxhQUFhLENBQUMsSUFBSSxDQUN0QixNQUFNLENBQUMsUUFBUSxDQUFDLGVBQWUsQ0FBQyxtQkFBbUIsRUFBRSxLQUFLLElBQUksRUFBRTtRQUM1RCxNQUFNLFlBQVksR0FBRyxNQUFNLE1BQU0sQ0FBQyxNQUFNLENBQUMsWUFBWSxDQUFDO1lBQ2xELE1BQU0sRUFBRSwyQ0FBMkM7WUFDbkQsS0FBSyxFQUFFLE1BQU0sQ0FBQyxJQUFJLENBQUM7WUFDbkIsYUFBYSxFQUFFLENBQUMsS0FBSyxFQUFFLEVBQUU7Z0JBQ3JCLE1BQU0sR0FBRyxHQUFHLE1BQU0sQ0FBQyxLQUFLLENBQUMsQ0FBQztnQkFDMUIsSUFBSSxLQUFLLENBQUMsR0FBRyxDQUFDLElBQUksR0FBRyxHQUFHLENBQUMsSUFBSSxHQUFHLEdBQUcsS0FBSyxFQUFFLENBQUM7b0JBQ3ZDLE9BQU8sNkNBQTZDLENBQUM7Z0JBQ3pELENBQUM7Z0JBQ0QsT0FBTyxJQUFJLENBQUM7WUFDaEIsQ0FBQztTQUNKLENBQUMsQ0FBQztRQUNILElBQUksWUFBWSxJQUFJLFlBQVksQ0FBQyxJQUFJLEVBQUUsQ0FBQyxNQUFNLEdBQUcsQ0FBQyxFQUFFLENBQUM7WUFDakQsTUFBTSxPQUFPLEdBQUcsTUFBTSxDQUFDLFlBQVksQ0FBQyxDQUFDO1lBRXJDLE1BQU0sTUFBTSxDQUFDLFNBQVM7aUJBQ2pCLGdCQUFnQixDQUFDLFdBQVcsQ0FBQztpQkFDN0IsTUFBTSxDQUFDLE1BQU0sRUFBRSxPQUFPLEVBQUUsTUFBTSxDQUFDLG1CQUFtQixDQUFDLE1BQU0sQ0FBQyxDQUFDO1lBRWhFLE1BQU0sQ0FBQyxLQUFLLEVBQUUsQ0FBQztZQUNmLFdBQVcsQ0FBQyxPQUFPLENBQUMsQ0FBQztZQUNyQixhQUFhLENBQUMsVUFBVSxDQUFDLGdDQUFnQyxPQUFPLEVBQUUsQ0FBQyxDQUFDO1lBQ3BFLE1BQU0sQ0FBQyxNQUFNLENBQUMsc0JBQXNCLENBQUMsZ0NBQWdDLE9BQU8sRUFBRSxDQUFDLENBQUM7UUFDcEYsQ0FBQztJQUNMLENBQUMsQ0FBQyxDQUNMLENBQUM7SUFFRixhQUFhLENBQUMsVUFBVSxDQUFDLEdBQUcsb0JBQW9CLGFBQWEsQ0FBQyxDQUFDO0FBQ25FLENBQUMsQ0FBQztBQUVGLE1BQU0sVUFBVSxVQUFVO0FBRTFCLENBQUMiLCJzb3VyY2VzQ29udGVudCI6WyJpbXBvcnQgeyBNY3BTZXJ2ZXIgfSBmcm9tICdAbW9kZWxjb250ZXh0cHJvdG9jb2wvc2RrL3NlcnZlci9tY3AuanMnO1xuaW1wb3J0IHsgU1NFU2VydmVyVHJhbnNwb3J0IH0gZnJvbSAnQG1vZGVsY29udGV4dHByb3RvY29sL3Nkay9zZXJ2ZXIvc3NlLmpzJztcbmltcG9ydCBkZWRlbnQgZnJvbSAnZGVkZW50JztcbmltcG9ydCBleHByZXNzLCB7IFJlcXVlc3QsIFJlc3BvbnNlIH0gZnJvbSAnZXhwcmVzcyc7XG5pbXBvcnQgKiBhcyBodHRwIGZyb20gJ2h0dHAnO1xuaW1wb3J0ICogYXMgdnNjb2RlIGZyb20gJ3ZzY29kZSc7XG5pbXBvcnQgeyBEaWFnbm9zdGljU2V2ZXJpdHkgfSBmcm9tICd2c2NvZGUnO1xuaW1wb3J0IHsgeiB9IGZyb20gJ3pvZCc7XG5pbXBvcnQgcGFja2FnZUpzb24gZnJvbSAnLi4vcGFja2FnZS5qc29uJztcbmltcG9ydCB7IGNvZGVDaGVja2VyVG9vbCB9IGZyb20gJy4vdG9vbHMvY29kZV9jaGVja2VyJztcbmltcG9ydCB7XG4gICAgbGlzdERlYnVnU2Vzc2lvbnMsXG4gICAgbGlzdERlYnVnU2Vzc2lvbnNTY2hlbWEsXG4gICAgc3RhcnREZWJ1Z1Nlc3Npb24sXG4gICAgc3RhcnREZWJ1Z1Nlc3Npb25TY2hlbWEsXG4gICAgc3RvcERlYnVnU2Vzc2lvbixcbiAgICBzdG9wRGVidWdTZXNzaW9uU2NoZW1hLFxufSBmcm9tICcuL3Rvb2xzL2RlYnVnX3Rvb2xzJztcbmltcG9ydCB7IGZvY3VzRWRpdG9yVG9vbCB9IGZyb20gJy4vdG9vbHMvZm9jdXNfZWRpdG9yJztcbmltcG9ydCB7IHJlc29sdmVQb3J0IH0gZnJvbSAnLi91dGlscy9wb3J0JztcblxuY29uc3QgZXh0ZW5zaW9uTmFtZSA9ICd2c2NvZGUtbWNwLXNlcnZlcic7XG5jb25zdCBleHRlbnNpb25EaXNwbGF5TmFtZSA9ICdWU0NvZGUgTUNQIFNlcnZlcic7XG5cbmV4cG9ydCBjb25zdCBhY3RpdmF0ZSA9IGFzeW5jIChjb250ZXh0OiB2c2NvZGUuRXh0ZW5zaW9uQ29udGV4dCkgPT4ge1xuICAgIC8vIENyZWF0ZSB0aGUgb3V0cHV0IGNoYW5uZWwgZm9yIGxvZ2dpbmdcbiAgICBjb25zdCBvdXRwdXRDaGFubmVsID0gdnNjb2RlLndpbmRvdy5jcmVhdGVPdXRwdXRDaGFubmVsKGV4dGVuc2lvbkRpc3BsYXlOYW1lKTtcblxuICAgIC8vIFdyaXRlIGFuIGluaXRpYWwgbWVzc2FnZSB0byBlbnN1cmUgdGhlIGNoYW5uZWwgYXBwZWFycyBpbiB0aGUgT3V0cHV0IGRyb3Bkb3duXG4gICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKGBBY3RpdmF0aW5nICR7ZXh0ZW5zaW9uRGlzcGxheU5hbWV9Li4uYCk7XG4gICAgLy8gVW5jb21tZW50IHRvIGF1dG9tYXRpY2FsbHkgc3dpdGNoIHRvIHRoZSBvdXRwdXQgdGFiIGFuZCB0aGlzIGV4dGVuc2lvbiBjaGFubmVsIG9uIGFjdGl2YXRpb25cbiAgICAvLyBvdXRwdXRDaGFubmVsLnNob3coKTtcblxuICAgIC8vIEluaXRpYWxpemUgdGhlIE1DUCBzZXJ2ZXIgaW5zdGFuY2VcbiAgICBjb25zdCBtY3BTZXJ2ZXIgPSBuZXcgTWNwU2VydmVyKHtcbiAgICAgICAgbmFtZTogZXh0ZW5zaW9uTmFtZSxcbiAgICAgICAgdmVyc2lvbjogcGFja2FnZUpzb24udmVyc2lvbixcbiAgICB9KTtcblxuICAgIC8vIFJlZ2lzdGVyIHRoZSBcImNvZGVfY2hlY2tlclwiIHRvb2wuXG4gICAgLy8gVGhpcyB0b29sIHJldHJpZXZlcyBkaWFnbm9zdGljcyBmcm9tIFZTQ29kZSdzIGxhbmd1YWdlIHNlcnZpY2VzLFxuICAgIC8vIGZpbHRlcmluZyBvdXQgZmlsZXMgd2l0aG91dCBpc3N1ZXMuXG4gICAgbWNwU2VydmVyLnRvb2woXG4gICAgICAgICdjb2RlX2NoZWNrZXInLFxuICAgICAgICBkZWRlbnRgXG4gICAgICAgICAgICBSZXRyaWV2ZSBkaWFnbm9zdGljcyBmcm9tIFZTQ29kZSdzIGxhbmd1YWdlIHNlcnZpY2VzIGZvciB0aGUgYWN0aXZlIHdvcmtzcGFjZS5cbiAgICAgICAgICAgIFVzZSB0aGlzIHRvb2wgYWZ0ZXIgbWFraW5nIGNoYW5nZXMgdG8gYW55IGNvZGUgaW4gdGhlIGZpbGVzeXN0ZW0gdG8gZW5zdXJlIG5vIG5ld1xuICAgICAgICAgICAgZXJyb3JzIHdlcmUgaW50cm9kdWNlZCwgb3Igd2hlbiByZXF1ZXN0ZWQgYnkgdGhlIHVzZXIuXG4gICAgICAgIGAudHJpbSgpLFxuICAgICAgICAvLyBQYXNzaW5nIHRoZSByYXcgc2hhcGUgb2JqZWN0IGRpcmVjdGx5XG4gICAgICAgIHtcbiAgICAgICAgICAgIHNldmVyaXR5TGV2ZWw6IHpcbiAgICAgICAgICAgICAgICAuZW51bShbJ0Vycm9yJywgJ1dhcm5pbmcnLCAnSW5mb3JtYXRpb24nLCAnSGludCddKVxuICAgICAgICAgICAgICAgIC5kZWZhdWx0KCdXYXJuaW5nJylcbiAgICAgICAgICAgICAgICAuZGVzY3JpYmUoXCJNaW5pbXVtIHNldmVyaXR5IGxldmVsIGZvciBjaGVja2luZyBpc3N1ZXM6ICdFcnJvcicsICdXYXJuaW5nJywgJ0luZm9ybWF0aW9uJywgb3IgJ0hpbnQnLlwiKSxcbiAgICAgICAgfSxcbiAgICAgICAgYXN5bmMgKHBhcmFtczogeyBzZXZlcml0eUxldmVsPzogJ0Vycm9yJyB8ICdXYXJuaW5nJyB8ICdJbmZvcm1hdGlvbicgfCAnSGludCcgfSkgPT4ge1xuICAgICAgICAgICAgY29uc3Qgc2V2ZXJpdHlMZXZlbCA9IHBhcmFtcy5zZXZlcml0eUxldmVsXG4gICAgICAgICAgICAgICAgPyBEaWFnbm9zdGljU2V2ZXJpdHlbcGFyYW1zLnNldmVyaXR5TGV2ZWxdXG4gICAgICAgICAgICAgICAgOiBEaWFnbm9zdGljU2V2ZXJpdHkuV2FybmluZztcbiAgICAgICAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IGNvZGVDaGVja2VyVG9vbChzZXZlcml0eUxldmVsKTtcbiAgICAgICAgICAgIHJldHVybiB7XG4gICAgICAgICAgICAgICAgLi4ucmVzdWx0LFxuICAgICAgICAgICAgICAgIGNvbnRlbnQ6IHJlc3VsdC5jb250ZW50Lm1hcCgoYykgPT4gKHtcbiAgICAgICAgICAgICAgICAgICAgLi4uYyxcbiAgICAgICAgICAgICAgICAgICAgdGV4dDogdHlwZW9mIGMudGV4dCA9PT0gJ3N0cmluZycgPyBjLnRleHQgOiBTdHJpbmcoYy50ZXh0KSxcbiAgICAgICAgICAgICAgICAgICAgdHlwZTogJ3RleHQnLFxuICAgICAgICAgICAgICAgIH0pKSxcbiAgICAgICAgICAgIH07XG4gICAgICAgIH0sXG4gICAgKTtcblxuICAgIC8vIFJlZ2lzdGVyICdmb2N1c19lZGl0b3InIHRvb2xcbiAgICBtY3BTZXJ2ZXIudG9vbChcbiAgICAgICAgJ2ZvY3VzX2VkaXRvcicsXG4gICAgICAgIGRlZGVudGBcbiAgICAgICAgT3BlbiB0aGUgc3BlY2lmaWVkIGZpbGUgaW4gdGhlIFZTQ29kZSBlZGl0b3IgYW5kIG5hdmlnYXRlIHRvIGEgc3BlY2lmaWMgbGluZSBhbmQgY29sdW1uLlxuICAgICAgICBVc2UgdGhpcyB0b29sIHRvIGJyaW5nIGEgZmlsZSBpbnRvIGZvY3VzIGFuZCBwb3NpdGlvbiB0aGUgZWRpdG9yJ3MgY3Vyc29yIHdoZXJlIGRlc2lyZWQuXG4gICAgICAgIE5vdGU6IFRoaXMgdG9vbCBvcGVyYXRlcyBvbiB0aGUgZWRpdG9yIHZpc3VhbCBlbnZpcm9ubWVudCBzbyB0aGF0IHRoZSB1c2VyIGNhbiBzZWUgdGhlIGZpbGUuIEl0IGRvZXMgbm90IHJldHVybiB0aGUgZmlsZSBjb250ZW50cyBpbiB0aGUgdG9vbCBjYWxsIHJlc3VsdC5cbiAgICAgICAgYC50cmltKCksXG4gICAgICAgIHtcbiAgICAgICAgICAgIGZpbGVQYXRoOiB6LnN0cmluZygpLmRlc2NyaWJlKCdUaGUgYWJzb2x1dGUgcGF0aCB0byB0aGUgZmlsZSB0byBmb2N1cyBpbiB0aGUgZWRpdG9yLicpLFxuICAgICAgICAgICAgbGluZTogei5udW1iZXIoKS5pbnQoKS5taW4oMCkuZGVmYXVsdCgwKS5kZXNjcmliZSgnVGhlIGxpbmUgbnVtYmVyIHRvIG5hdmlnYXRlIHRvIChkZWZhdWx0OiAwKS4nKSxcbiAgICAgICAgICAgIGNvbHVtbjogei5udW1iZXIoKS5pbnQoKS5taW4oMCkuZGVmYXVsdCgwKS5kZXNjcmliZSgnVGhlIGNvbHVtbiBwb3NpdGlvbiB0byBuYXZpZ2F0ZSB0byAoZGVmYXVsdDogMCkuJyksXG4gICAgICAgICAgICBzdGFydExpbmU6IHoubnVtYmVyKCkuaW50KCkubWluKDApLm9wdGlvbmFsKCkuZGVzY3JpYmUoJ1RoZSBzdGFydGluZyBsaW5lIG51bWJlciBmb3IgaGlnaGxpZ2h0aW5nLicpLFxuICAgICAgICAgICAgc3RhcnRDb2x1bW46IHoubnVtYmVyKCkuaW50KCkubWluKDApLm9wdGlvbmFsKCkuZGVzY3JpYmUoJ1RoZSBzdGFydGluZyBjb2x1bW4gbnVtYmVyIGZvciBoaWdobGlnaHRpbmcuJyksXG4gICAgICAgICAgICBlbmRMaW5lOiB6Lm51bWJlcigpLmludCgpLm1pbigwKS5vcHRpb25hbCgpLmRlc2NyaWJlKCdUaGUgZW5kaW5nIGxpbmUgbnVtYmVyIGZvciBoaWdobGlnaHRpbmcuJyksXG4gICAgICAgICAgICBlbmRDb2x1bW46IHoubnVtYmVyKCkuaW50KCkubWluKDApLm9wdGlvbmFsKCkuZGVzY3JpYmUoJ1RoZSBlbmRpbmcgY29sdW1uIG51bWJlciBmb3IgaGlnaGxpZ2h0aW5nLicpLFxuICAgICAgICB9LFxuICAgICAgICBhc3luYyAocGFyYW1zOiB7IGZpbGVQYXRoOiBzdHJpbmc7IGxpbmU/OiBudW1iZXI7IGNvbHVtbj86IG51bWJlciB9KSA9PiB7XG4gICAgICAgICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCBmb2N1c0VkaXRvclRvb2wocGFyYW1zKTtcbiAgICAgICAgICAgIHJldHVybiByZXN1bHQ7XG4gICAgICAgIH0sXG4gICAgKTtcblxuICAgIC8vIEZJWE1FOiBUaGlzIGRvZXNuJ3QgcmV0dXJuIHJlc3VsdHMgeWV0XG4gICAgLy8gLy8gUmVnaXN0ZXIgJ3NlYXJjaF9zeW1ib2wnIHRvb2xcbiAgICAvLyBtY3BTZXJ2ZXIudG9vbChcbiAgICAvLyAgICAgJ3NlYXJjaF9zeW1ib2wnLFxuICAgIC8vICAgICBkZWRlbnRgXG4gICAgLy8gICAgIFNlYXJjaCBmb3IgYSBzeW1ib2wgd2l0aGluIHRoZSB3b3Jrc3BhY2UuXG4gICAgLy8gICAgIC0gVHJpZXMgdG8gcmVzb2x2ZSB0aGUgZGVmaW5pdGlvbiB2aWEgVlNDb2Rl4oCZcyBcIkdvIHRvIERlZmluaXRpb25cIi5cbiAgICAvLyAgICAgLSBJZiBub3QgZm91bmQsIHNlYXJjaGVzIHRoZSBlbnRpcmUgd29ya3NwYWNlIGZvciB0aGUgdGV4dCwgc2ltaWxhciB0byBDdHJsK1NoaWZ0K0YuXG4gICAgLy8gICAgIGAudHJpbSgpLFxuICAgIC8vICAgICB7XG4gICAgLy8gICAgICAgICBxdWVyeTogei5zdHJpbmcoKS5kZXNjcmliZSgnVGhlIHN5bWJvbCBvciB0ZXh0IHRvIHNlYXJjaCBmb3IuJyksXG4gICAgLy8gICAgICAgICB1c2VEZWZpbml0aW9uOiB6LmJvb2xlYW4oKS5kZWZhdWx0KHRydWUpLmRlc2NyaWJlKFwiV2hldGhlciB0byB1c2UgJ0dvIHRvIERlZmluaXRpb24nIGFzIHRoZSBmaXJzdCBtZXRob2QuXCIpLFxuICAgIC8vICAgICAgICAgbWF4UmVzdWx0czogei5udW1iZXIoKS5kZWZhdWx0KDUwKS5kZXNjcmliZSgnTWF4aW11bSBudW1iZXIgb2YgZ2xvYmFsIHNlYXJjaCByZXN1bHRzIHRvIHJldHVybi4nKSxcbiAgICAvLyAgICAgICAgIG9wZW5GaWxlOiB6LmJvb2xlYW4oKS5kZWZhdWx0KGZhbHNlKS5kZXNjcmliZSgnV2hldGhlciB0byBvcGVuIHRoZSBmb3VuZCBmaWxlIGluIHRoZSBlZGl0b3IuJyksXG4gICAgLy8gICAgIH0sXG4gICAgLy8gICAgIGFzeW5jIChwYXJhbXM6IHsgcXVlcnk6IHN0cmluZzsgdXNlRGVmaW5pdGlvbj86IGJvb2xlYW47IG1heFJlc3VsdHM/OiBudW1iZXI7IG9wZW5GaWxlPzogYm9vbGVhbiB9KSA9PiB7XG4gICAgLy8gICAgICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCBzZWFyY2hTeW1ib2xUb29sKHBhcmFtcyk7XG4gICAgLy8gICAgICAgICByZXR1cm4ge1xuICAgIC8vICAgICAgICAgICAgIC4uLnJlc3VsdCxcbiAgICAvLyAgICAgICAgICAgICBjb250ZW50OiBbXG4gICAgLy8gICAgICAgICAgICAgICAgIHtcbiAgICAvLyAgICAgICAgICAgICAgICAgICAgIHRleHQ6IEpTT04uc3RyaW5naWZ5KHJlc3VsdCksXG4gICAgLy8gICAgICAgICAgICAgICAgICAgICB0eXBlOiAndGV4dCcsXG4gICAgLy8gICAgICAgICAgICAgICAgIH0sXG4gICAgLy8gICAgICAgICAgICAgXSxcbiAgICAvLyAgICAgICAgIH07XG4gICAgLy8gICAgIH0sXG4gICAgLy8gKTtcblxuICAgIC8vIFJlZ2lzdGVyICdsaXN0X2RlYnVnX3Nlc3Npb25zJyB0b29sXG4gICAgbWNwU2VydmVyLnRvb2woXG4gICAgICAgICdsaXN0X2RlYnVnX3Nlc3Npb25zJyxcbiAgICAgICAgJ0xpc3QgYWxsIGFjdGl2ZSBkZWJ1ZyBzZXNzaW9ucyBpbiB0aGUgd29ya3NwYWNlLicsXG4gICAgICAgIGxpc3REZWJ1Z1Nlc3Npb25zU2NoZW1hLnNoYXBlLCAvLyBObyBwYXJhbWV0ZXJzIHJlcXVpcmVkXG4gICAgICAgIGFzeW5jICgpID0+IHtcbiAgICAgICAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IGxpc3REZWJ1Z1Nlc3Npb25zKCk7XG4gICAgICAgICAgICByZXR1cm4ge1xuICAgICAgICAgICAgICAgIC4uLnJlc3VsdCxcbiAgICAgICAgICAgICAgICBjb250ZW50OiByZXN1bHQuY29udGVudC5tYXAoKGl0ZW0pID0+ICh7IHR5cGU6ICd0ZXh0JywgdGV4dDogSlNPTi5zdHJpbmdpZnkoaXRlbS5qc29uKSB9KSksXG4gICAgICAgICAgICB9O1xuICAgICAgICB9LFxuICAgICk7XG5cbiAgICAvLyBSZWdpc3RlciAnc3RhcnRfZGVidWdfc2Vzc2lvbicgdG9vbFxuICAgIG1jcFNlcnZlci50b29sKFxuICAgICAgICAnc3RhcnRfZGVidWdfc2Vzc2lvbicsXG4gICAgICAgICdTdGFydCBhIG5ldyBkZWJ1ZyBzZXNzaW9uIHdpdGggdGhlIHByb3ZpZGVkIGNvbmZpZ3VyYXRpb24uJyxcbiAgICAgICAgc3RhcnREZWJ1Z1Nlc3Npb25TY2hlbWEuc2hhcGUsXG4gICAgICAgIGFzeW5jIChwYXJhbXMpID0+IHtcbiAgICAgICAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHN0YXJ0RGVidWdTZXNzaW9uKHBhcmFtcyk7XG4gICAgICAgICAgICByZXR1cm4ge1xuICAgICAgICAgICAgICAgIC4uLnJlc3VsdCxcbiAgICAgICAgICAgICAgICBjb250ZW50OiByZXN1bHQuY29udGVudC5tYXAoKGl0ZW0pID0+ICh7XG4gICAgICAgICAgICAgICAgICAgIC4uLml0ZW0sXG4gICAgICAgICAgICAgICAgICAgIHR5cGU6ICd0ZXh0JyBhcyBjb25zdCxcbiAgICAgICAgICAgICAgICB9KSksXG4gICAgICAgICAgICB9O1xuICAgICAgICB9LFxuICAgICk7XG5cbiAgICAvLyBSZWdpc3RlciAnc3RvcF9kZWJ1Z19zZXNzaW9uJyB0b29sXG5cbiAgICAvLyBSZWdpc3RlciAncmVzdGFydF9kZWJ1Z19zZXNzaW9uJyB0b29sXG4gICAgbWNwU2VydmVyLnRvb2woXG4gICAgICAgICdyZXN0YXJ0X2RlYnVnX3Nlc3Npb24nLFxuICAgICAgICAnUmVzdGFydCBhIGRlYnVnIHNlc3Npb24gYnkgc3RvcHBpbmcgaXQgYW5kIHRoZW4gc3RhcnRpbmcgaXQgd2l0aCB0aGUgcHJvdmlkZWQgY29uZmlndXJhdGlvbi4nLFxuICAgICAgICBzdGFydERlYnVnU2Vzc2lvblNjaGVtYS5zaGFwZSwgLy8gdXNpbmcgdGhlIHNhbWUgc2NoZW1hIGFzICdzdGFydF9kZWJ1Z19zZXNzaW9uJ1xuICAgICAgICBhc3luYyAocGFyYW1zKSA9PiB7XG4gICAgICAgICAgICAvLyBTdG9wIGN1cnJlbnQgc2Vzc2lvbiB1c2luZyB0aGUgcHJvdmlkZWQgc2Vzc2lvbiBuYW1lXG4gICAgICAgICAgICBhd2FpdCBzdG9wRGVidWdTZXNzaW9uKHsgc2Vzc2lvbk5hbWU6IHBhcmFtcy5jb25maWd1cmF0aW9uLm5hbWUgfSk7XG5cbiAgICAgICAgICAgIC8vIFRoZW4gc3RhcnQgYSBuZXcgZGVidWcgc2Vzc2lvbiB3aXRoIHRoZSBnaXZlbiBjb25maWd1cmF0aW9uXG4gICAgICAgICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCBzdGFydERlYnVnU2Vzc2lvbihwYXJhbXMpO1xuICAgICAgICAgICAgcmV0dXJuIHtcbiAgICAgICAgICAgICAgICAuLi5yZXN1bHQsXG4gICAgICAgICAgICAgICAgY29udGVudDogcmVzdWx0LmNvbnRlbnQubWFwKChpdGVtKSA9PiAoe1xuICAgICAgICAgICAgICAgICAgICAuLi5pdGVtLFxuICAgICAgICAgICAgICAgICAgICB0eXBlOiAndGV4dCcgYXMgY29uc3QsXG4gICAgICAgICAgICAgICAgfSkpLFxuICAgICAgICAgICAgfTtcbiAgICAgICAgfSxcbiAgICApO1xuICAgIG1jcFNlcnZlci50b29sKFxuICAgICAgICAnc3RvcF9kZWJ1Z19zZXNzaW9uJyxcbiAgICAgICAgJ1N0b3AgYWxsIGRlYnVnIHNlc3Npb25zIHRoYXQgbWF0Y2ggdGhlIHByb3ZpZGVkIHNlc3Npb24gbmFtZS4nLFxuICAgICAgICBzdG9wRGVidWdTZXNzaW9uU2NoZW1hLnNoYXBlLFxuICAgICAgICBhc3luYyAocGFyYW1zKSA9PiB7XG4gICAgICAgICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCBzdG9wRGVidWdTZXNzaW9uKHBhcmFtcyk7XG4gICAgICAgICAgICByZXR1cm4ge1xuICAgICAgICAgICAgICAgIC4uLnJlc3VsdCxcbiAgICAgICAgICAgICAgICBjb250ZW50OiByZXN1bHQuY29udGVudC5tYXAoKGl0ZW0pID0+ICh7XG4gICAgICAgICAgICAgICAgICAgIC4uLml0ZW0sXG4gICAgICAgICAgICAgICAgICAgIHR5cGU6ICd0ZXh0JyBhcyBjb25zdCxcbiAgICAgICAgICAgICAgICB9KSksXG4gICAgICAgICAgICB9O1xuICAgICAgICB9LFxuICAgICk7XG5cbiAgICAvLyBTZXQgdXAgYW4gRXhwcmVzcyBhcHAgdG8gaGFuZGxlIFNTRSBjb25uZWN0aW9uc1xuICAgIGNvbnN0IGFwcCA9IGV4cHJlc3MoKTtcbiAgICBjb25zdCBtY3BDb25maWcgPSB2c2NvZGUud29ya3NwYWNlLmdldENvbmZpZ3VyYXRpb24oJ21jcFNlcnZlcicpO1xuICAgIGNvbnN0IHBvcnQgPSBhd2FpdCByZXNvbHZlUG9ydChtY3BDb25maWcuZ2V0PG51bWJlcj4oJ3BvcnQnLCA2MDEwKSk7XG5cbiAgICBsZXQgc3NlVHJhbnNwb3J0OiBTU0VTZXJ2ZXJUcmFuc3BvcnQgfCB1bmRlZmluZWQ7XG5cbiAgICAvLyBHRVQgL3NzZSBlbmRwb2ludDogdGhlIGV4dGVybmFsIE1DUCBjbGllbnQgY29ubmVjdHMgaGVyZSAoU1NFKVxuICAgIGFwcC5nZXQoJy9zc2UnLCBhc3luYyAoX3JlcTogUmVxdWVzdCwgcmVzOiBSZXNwb25zZSkgPT4ge1xuICAgICAgICBvdXRwdXRDaGFubmVsLmFwcGVuZExpbmUoJ1NTRSBjb25uZWN0aW9uIGluaXRpYXRlZC4uLicpO1xuICAgICAgICBzc2VUcmFuc3BvcnQgPSBuZXcgU1NFU2VydmVyVHJhbnNwb3J0KCcvbWVzc2FnZXMnLCByZXMpO1xuICAgICAgICB0cnkge1xuICAgICAgICAgICAgYXdhaXQgbWNwU2VydmVyLmNvbm5lY3Qoc3NlVHJhbnNwb3J0KTtcbiAgICAgICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZSgnTUNQIFNlcnZlciBjb25uZWN0ZWQgdmlhIFNTRS4nKTtcbiAgICAgICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZShgU1NFIFRyYW5zcG9ydCBzZXNzaW9uSWQ6ICR7c3NlVHJhbnNwb3J0LnNlc3Npb25JZH1gKTtcbiAgICAgICAgfSBjYXRjaCAoZXJyKSB7XG4gICAgICAgICAgICBvdXRwdXRDaGFubmVsLmFwcGVuZExpbmUoJ0Vycm9yIGNvbm5lY3RpbmcgTUNQIFNlcnZlciB2aWEgU1NFOiAnICsgZXJyKTtcbiAgICAgICAgfVxuICAgIH0pO1xuXG4gICAgLy8gUE9TVCAvbWVzc2FnZXMgZW5kcG9pbnQ6IHRoZSBleHRlcm5hbCBNQ1AgY2xpZW50IHNlbmRzIG1lc3NhZ2VzIGhlcmVcbiAgICBhcHAucG9zdCgnL21lc3NhZ2VzJywgZXhwcmVzcy5qc29uKCksIGFzeW5jIChyZXE6IFJlcXVlc3QsIHJlczogUmVzcG9uc2UpID0+IHtcbiAgICAgICAgLy8gTG9nIGluIG91dHB1dCBjaGFubmVsXG4gICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZShgUE9TVCAvbWVzc2FnZXM6IFBheWxvYWQgLSAke0pTT04uc3RyaW5naWZ5KHJlcS5ib2R5LCBudWxsLCAyKX1gKTtcblxuICAgICAgICBpZiAoc3NlVHJhbnNwb3J0KSB7XG4gICAgICAgICAgICAvLyBMb2cgdGhlIHNlc3Npb24gSUQgb2YgdGhlIHRyYW5zcG9ydCB0byBjb25maXJtIGl0cyBpbml0aWFsaXphdGlvblxuICAgICAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKGBTU0UgVHJhbnNwb3J0IHNlc3Npb25JZDogJHtzc2VUcmFuc3BvcnQuc2Vzc2lvbklkfWApO1xuICAgICAgICAgICAgdHJ5IHtcbiAgICAgICAgICAgICAgICAvLyBOb3RlOiBQYXNzaW5nIHJlcS5ib2R5IHRvIGhhbmRsZVBvc3RNZXNzYWdlIGlzIGNyaXRpY2FsIGJlY2F1c2UgZXhwcmVzcy5qc29uKClcbiAgICAgICAgICAgICAgICAvLyBjb25zdW1lcyB0aGUgcmVxdWVzdCBzdHJlYW0uIFdpdGhvdXQgdGhpcywgYXR0ZW1wdGluZyB0byByZS1yZWFkIHRoZSBzdHJlYW1cbiAgICAgICAgICAgICAgICAvLyB3aXRoaW4gaGFuZGxlUG9zdE1lc3NhZ2Ugd291bGQgcmVzdWx0IGluIGEgXCJzdHJlYW0gaXMgbm90IHJlYWRhYmxlXCIgZXJyb3IuXG4gICAgICAgICAgICAgICAgYXdhaXQgc3NlVHJhbnNwb3J0LmhhbmRsZVBvc3RNZXNzYWdlKHJlcSwgcmVzLCByZXEuYm9keSk7XG4gICAgICAgICAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKCdIYW5kbGVkIFBPU1QgL21lc3NhZ2VzIHN1Y2Nlc3NmdWxseS4nKTtcbiAgICAgICAgICAgIH0gY2F0Y2ggKGVycikge1xuICAgICAgICAgICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZSgnRXJyb3IgaGFuZGxpbmcgUE9TVCAvbWVzc2FnZXM6ICcgKyBlcnIpO1xuICAgICAgICAgICAgfVxuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgcmVzLnN0YXR1cyg1MDApLnNlbmQoJ1NTRSBUcmFuc3BvcnQgbm90IGluaXRpYWxpemVkLicpO1xuICAgICAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKCdQT1NUIC9tZXNzYWdlcyBmYWlsZWQ6IFNTRSBUcmFuc3BvcnQgbm90IGluaXRpYWxpemVkLicpO1xuICAgICAgICB9XG4gICAgfSk7XG5cbiAgICAvLyBDcmVhdGUgYW5kIHN0YXJ0IHRoZSBIVFRQIHNlcnZlclxuICAgIGNvbnN0IHNlcnZlciA9IGh0dHAuY3JlYXRlU2VydmVyKGFwcCk7XG4gICAgZnVuY3Rpb24gc3RhcnRTZXJ2ZXIocG9ydDogbnVtYmVyKTogdm9pZCB7XG4gICAgICAgIHNlcnZlci5saXN0ZW4ocG9ydCwgKCkgPT4ge1xuICAgICAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKGBNQ1AgU1NFIFNlcnZlciBydW5uaW5nIGF0IGh0dHA6Ly8xMjcuMC4wLjE6JHtwb3J0fS9zc2VgKTtcbiAgICAgICAgfSk7XG5cbiAgICAgICAgLy8gQWRkIGRpc3Bvc2FsIHRvIHNodXQgZG93biB0aGUgSFRUUCBzZXJ2ZXIgYW5kIG91dHB1dCBjaGFubmVsIG9uIGV4dGVuc2lvbiBkZWFjdGl2YXRpb25cbiAgICAgICAgY29udGV4dC5zdWJzY3JpcHRpb25zLnB1c2goe1xuICAgICAgICAgICAgZGlzcG9zZTogKCkgPT4ge1xuICAgICAgICAgICAgICAgIHNlcnZlci5jbG9zZSgpO1xuICAgICAgICAgICAgICAgIG91dHB1dENoYW5uZWwuZGlzcG9zZSgpO1xuICAgICAgICAgICAgfSxcbiAgICAgICAgfSk7XG4gICAgfVxuICAgIGNvbnN0IHN0YXJ0T25BY3RpdmF0ZSA9IG1jcENvbmZpZy5nZXQ8Ym9vbGVhbj4oJ3N0YXJ0T25BY3RpdmF0ZScsIHRydWUpO1xuICAgIGlmIChzdGFydE9uQWN0aXZhdGUpIHtcbiAgICAgICAgc3RhcnRTZXJ2ZXIocG9ydCk7XG4gICAgfSBlbHNlIHtcbiAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKCdNQ1AgU2VydmVyIHN0YXJ0dXAgZGlzYWJsZWQgYnkgY29uZmlndXJhdGlvbi4nKTtcbiAgICB9XG5cbiAgICAvLyBDT01NQU5EIFBBTEVUVEUgQ09NTUFORDogU3RvcCB0aGUgTUNQIFNlcnZlclxuICAgIGNvbnRleHQuc3Vic2NyaXB0aW9ucy5wdXNoKFxuICAgICAgICB2c2NvZGUuY29tbWFuZHMucmVnaXN0ZXJDb21tYW5kKCdtY3BTZXJ2ZXIuc3RvcFNlcnZlcicsICgpID0+IHtcbiAgICAgICAgICAgIGlmICghc2VydmVyLmxpc3RlbmluZykge1xuICAgICAgICAgICAgICAgIHZzY29kZS53aW5kb3cuc2hvd1dhcm5pbmdNZXNzYWdlKCdNQ1AgU2VydmVyIGlzIG5vdCBydW5uaW5nLicpO1xuICAgICAgICAgICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZSgnQXR0ZW1wdGVkIHRvIHN0b3AgdGhlIE1DUCBTZXJ2ZXIsIGJ1dCBpdCBpcyBub3QgcnVubmluZy4nKTtcbiAgICAgICAgICAgICAgICByZXR1cm47XG4gICAgICAgICAgICB9XG4gICAgICAgICAgICBzZXJ2ZXIuY2xvc2UoKCkgPT4ge1xuICAgICAgICAgICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZSgnTUNQIFNlcnZlciBzdG9wcGVkLicpO1xuICAgICAgICAgICAgICAgIHZzY29kZS53aW5kb3cuc2hvd0luZm9ybWF0aW9uTWVzc2FnZSgnTUNQIFNlcnZlciBzdG9wcGVkLicpO1xuICAgICAgICAgICAgfSk7XG4gICAgICAgIH0pLFxuICAgICk7XG5cbiAgICAvLyBDT01NQU5EIFBBTEVUVEUgQ09NTUFORDogU3RhcnQgdGhlIE1DUCBTZXJ2ZXJcbiAgICBjb250ZXh0LnN1YnNjcmlwdGlvbnMucHVzaChcbiAgICAgICAgdnNjb2RlLmNvbW1hbmRzLnJlZ2lzdGVyQ29tbWFuZCgnbWNwU2VydmVyLnN0YXJ0U2VydmVyJywgYXN5bmMgKCkgPT4ge1xuICAgICAgICAgICAgaWYgKHNlcnZlci5saXN0ZW5pbmcpIHtcbiAgICAgICAgICAgICAgICB2c2NvZGUud2luZG93LnNob3dXYXJuaW5nTWVzc2FnZSgnTUNQIFNlcnZlciBpcyBhbHJlYWR5IHJ1bm5pbmcuJyk7XG4gICAgICAgICAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKCdBdHRlbXB0ZWQgdG8gc3RhcnQgdGhlIE1DUCBTZXJ2ZXIsIGJ1dCBpdCBpcyBhbHJlYWR5IHJ1bm5pbmcuJyk7XG4gICAgICAgICAgICAgICAgcmV0dXJuO1xuICAgICAgICAgICAgfVxuICAgICAgICAgICAgY29uc3QgbmV3UG9ydCA9IGF3YWl0IHJlc29sdmVQb3J0KG1jcENvbmZpZy5nZXQ8bnVtYmVyPigncG9ydCcsIDYwMTApKTtcbiAgICAgICAgICAgIHN0YXJ0U2VydmVyKG5ld1BvcnQpO1xuICAgICAgICAgICAgb3V0cHV0Q2hhbm5lbC5hcHBlbmRMaW5lKGBNQ1AgU2VydmVyIHN0YXJ0ZWQgb24gcG9ydCAke25ld1BvcnR9LmApO1xuICAgICAgICAgICAgdnNjb2RlLndpbmRvdy5zaG93SW5mb3JtYXRpb25NZXNzYWdlKGBNQ1AgU2VydmVyIHN0YXJ0ZWQgb24gcG9ydCAke25ld1BvcnR9LmApO1xuICAgICAgICB9KSxcbiAgICApO1xuXG4gICAgLy8gQ09NTUFORCBQQUxFVFRFIENPTU1BTkQ6IFNldCB0aGUgTUNQIHNlcnZlciBwb3J0IGFuZCByZXN0YXJ0IHRoZSBzZXJ2ZXJcbiAgICBjb250ZXh0LnN1YnNjcmlwdGlvbnMucHVzaChcbiAgICAgICAgdnNjb2RlLmNvbW1hbmRzLnJlZ2lzdGVyQ29tbWFuZCgnbWNwU2VydmVyLnNldFBvcnQnLCBhc3luYyAoKSA9PiB7XG4gICAgICAgICAgICBjb25zdCBuZXdQb3J0SW5wdXQgPSBhd2FpdCB2c2NvZGUud2luZG93LnNob3dJbnB1dEJveCh7XG4gICAgICAgICAgICAgICAgcHJvbXB0OiAnRW50ZXIgbmV3IHBvcnQgbnVtYmVyIGZvciB0aGUgTUNQIFNlcnZlcjonLFxuICAgICAgICAgICAgICAgIHZhbHVlOiBTdHJpbmcocG9ydCksXG4gICAgICAgICAgICAgICAgdmFsaWRhdGVJbnB1dDogKGlucHV0KSA9PiB7XG4gICAgICAgICAgICAgICAgICAgIGNvbnN0IG51bSA9IE51bWJlcihpbnB1dCk7XG4gICAgICAgICAgICAgICAgICAgIGlmIChpc05hTihudW0pIHx8IG51bSA8IDEgfHwgbnVtID4gNjU1MzUpIHtcbiAgICAgICAgICAgICAgICAgICAgICAgIHJldHVybiAnUGxlYXNlIGVudGVyIGEgdmFsaWQgcG9ydCBudW1iZXIgKDEtNjU1MzUpLic7XG4gICAgICAgICAgICAgICAgICAgIH1cbiAgICAgICAgICAgICAgICAgICAgcmV0dXJuIG51bGw7XG4gICAgICAgICAgICAgICAgfSxcbiAgICAgICAgICAgIH0pO1xuICAgICAgICAgICAgaWYgKG5ld1BvcnRJbnB1dCAmJiBuZXdQb3J0SW5wdXQudHJpbSgpLmxlbmd0aCA+IDApIHtcbiAgICAgICAgICAgICAgICBjb25zdCBuZXdQb3J0ID0gTnVtYmVyKG5ld1BvcnRJbnB1dCk7XG4gICAgICAgICAgICAgICAgLy8gVXBkYXRlIHRoZSBjb25maWd1cmF0aW9uIHNvIHRoYXQgc3Vic2VxdWVudCBzdGFydHVwcyB1c2UgdGhlIG5ldyBwb3J0XG4gICAgICAgICAgICAgICAgYXdhaXQgdnNjb2RlLndvcmtzcGFjZVxuICAgICAgICAgICAgICAgICAgICAuZ2V0Q29uZmlndXJhdGlvbignbWNwU2VydmVyJylcbiAgICAgICAgICAgICAgICAgICAgLnVwZGF0ZSgncG9ydCcsIG5ld1BvcnQsIHZzY29kZS5Db25maWd1cmF0aW9uVGFyZ2V0Lkdsb2JhbCk7XG4gICAgICAgICAgICAgICAgLy8gUmVzdGFydCB0aGUgc2VydmVyOiBjbG9zZSBleGlzdGluZyBzZXJ2ZXIgYW5kIHN0YXJ0IGEgbmV3IG9uZVxuICAgICAgICAgICAgICAgIHNlcnZlci5jbG9zZSgpO1xuICAgICAgICAgICAgICAgIHN0YXJ0U2VydmVyKG5ld1BvcnQpO1xuICAgICAgICAgICAgICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZShgTUNQIFNlcnZlciByZXN0YXJ0ZWQgb24gcG9ydCAke25ld1BvcnR9YCk7XG4gICAgICAgICAgICAgICAgdnNjb2RlLndpbmRvdy5zaG93SW5mb3JtYXRpb25NZXNzYWdlKGBNQ1AgU2VydmVyIHJlc3RhcnRlZCBvbiBwb3J0ICR7bmV3UG9ydH1gKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgfSksXG4gICAgKTtcblxuICAgIG91dHB1dENoYW5uZWwuYXBwZW5kTGluZShgJHtleHRlbnNpb25EaXNwbGF5TmFtZX0gYWN0aXZhdGVkLmApO1xufTtcblxuZXhwb3J0IGZ1bmN0aW9uIGRlYWN0aXZhdGUoKSB7XG4gICAgLy8gQ2xlYW4tdXAgaXMgbWFuYWdlZCBieSB0aGUgZGlzcG9zYWJsZXMgYWRkZWQgaW4gdGhlIGFjdGl2YXRlIG1ldGhvZC5cbn1cbiJdfQ==