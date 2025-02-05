import * as vscode from 'vscode';
import express from 'express';
import * as http from 'http';
import { Request, Response } from 'express';
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { SSEServerTransport } from "@modelcontextprotocol/sdk/server/sse.js";

export function activate(context: vscode.ExtensionContext) {
    // Create an output channel for logging activity
    const outputChannel = vscode.window.createOutputChannel("MCP Server Logs");
    outputChannel.appendLine("Activating Codespace Assistant: Coder MCP Server...");

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
        } catch (err) {
            outputChannel.appendLine("Error connecting MCP Server via SSE: " + err);
        }
    });

    // POST /messages endpoint: receives messages from the external assistant
    app.post('/messages', express.json(), async (req: Request, res: Response) => {
        if (sseTransport) {
            try {
                await sseTransport.handlePostMessage(req, res);
                outputChannel.appendLine("Handled POST /messages.");
            } catch (err) {
                outputChannel.appendLine("Error handling POST /messages: " + err);
            }
        } else {
            res.status(500).send("SSE Transport not initialized.");
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