import * as vscode from 'vscode';
import express from 'express';
import * as http from 'http';
import { Request, Response } from 'express';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

export function activate(context: vscode.ExtensionContext) {
    // Create the MCP Server Logs output channel
    const outputChannel = vscode.window.createOutputChannel("MCP Server Logs");

    // Write an initial message to ensure the channel appears in the Output dropdown
    outputChannel.appendLine("Activating Codespace Assistant: Coder MCP Server...");
    outputChannel.show();

    // Register the "MCP: Aggregate Diagnostics" command (placeholder action)
    const diagnosticsCommand = vscode.commands.registerCommand("mcp.aggregateDiagnostics", () => {
        // Placeholder logic to avoid "command not found" errors.
        outputChannel.appendLine("MCP: Aggregate Diagnostics command invoked.");
        outputChannel.show();
    });
    context.subscriptions.push(diagnosticsCommand);

    // Initialize the MCP server instance
    const mcpServer = new McpServer({
        name: "VSCode Diagnostic MCP Server",
        version: "0.0.1",
    });

    // Register the "code_checker" tool.
    // This tool retrieves diagnostics from VSCode's language services,
    // filtering out files without issues.
    mcpServer.tool("code_checker", {}, async () => {
        // Retrieve diagnostics from all files
        const diagnosticsByFile = vscode.languages.getDiagnostics();
        // Filter to only include files that have diagnostics
        const aggregated = diagnosticsByFile
            .filter(([uri, diags]) => diags.length > 0)
            .map(([uri, diags]) => ({
                file: uri.fsPath,
                diagnostics: diags.map(diag => ({
                    severity: vscode.DiagnosticSeverity[diag.severity],
                    message: diag.message,
                    source: diag.source || ""
                }))
            }));

        if (aggregated.length === 0) {
            // If no diagnostics found, return an empty result
            return { content: [{ type: "text", text: "No issues found." }] };
        }

        // Otherwise, return the aggregated diagnostics as formatted JSON
        return { content: [{ type: "text", text: JSON.stringify(aggregated, null, 2) }] };
    });

    // Set up an Express app to handle SSE connections
    const app = express();
    const port = 6010;
    let sseTransport: SSEServerTransport | undefined;

    // GET /sse endpoint: the external assistant connects here (SSE)
    app.get('/sse', async (req: Request, res: Response) => {
        outputChannel.appendLine("SSE connection initiated...");
        sseTransport = new SSEServerTransport("/messages", res);
        try {
            await mcpServer.connect(sseTransport);
            outputChannel.appendLine("MCP Server connected via SSE.");
            // Log the session ID of the transport to confirm its initialization
            console.log("SSE Transport sessionId: ", sseTransport.sessionId);
            outputChannel.appendLine(`SSE Transport sessionId: ${sseTransport.sessionId}`);
        } catch (err) {
            outputChannel.appendLine("Error connecting MCP Server via SSE: " + err);
        }
    });

    app.post('/messages', express.json(), async (req: Request, res: Response) => {
        // Log the incoming payload
        console.log("Received POST request:", req.body);
        // Log in output channel
        outputChannel.appendLine(`POST /messages: Payload - ${JSON.stringify(req.body, null, 2)}`);
    
        if (sseTransport) {
            // Log the session ID of the transport to confirm its initialization
            console.log("SSE Transport sessionId: ", sseTransport.sessionId);
            outputChannel.appendLine(`SSE Transport sessionId: ${sseTransport.sessionId}`);
            try {
                // Note: Passing req.body to handlePostMessage is critical because express.json()
                // consumes the request stream. Without this, attempting to re-read the stream
                // within handlePostMessage would result in a "stream is not readable" error.
                await sseTransport.handlePostMessage(req, res, req.body);
                outputChannel.appendLine("Handled POST /messages successfully.");
            } catch (err) {
                outputChannel.appendLine("Error handling POST /messages: " + err);
                // Log error details
                console.error("Error during handlePostMessage:", err);
            }
        } else {
            res.status(500).send("SSE Transport not initialized.");
            outputChannel.appendLine("POST /messages failed: SSE Transport not initialized.");
            console.error("SSE Transport was not initialized when handling POST /messages.");
        }
    });

    // Create and start the HTTP server
    const server = http.createServer(app);
    server.listen(port, () => {
        outputChannel.appendLine(`MCP SSE Server running at http://127.0.0.1:${port}/sse`);
    });

    // Add disposal to shut down the HTTP server and output channel on extension deactivation
    context.subscriptions.push({
        dispose: () => {
            server.close();
            outputChannel.dispose();
        }
    });

    outputChannel.appendLine("Codespace Assistant: Coder MCP Server activated.");
}

export function deactivate() {
    // Clean-up is managed by the disposables added in the activate method.
}