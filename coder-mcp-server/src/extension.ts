import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
    // Create an output channel for diagnostics
    const outputChannel = vscode.window.createOutputChannel("MCP Diagnostics");

    // Register the command to aggregate diagnostics
    let disposable = vscode.commands.registerCommand("mcp.aggregateDiagnostics", () => {
        outputChannel.clear();

        // Retrieve diagnostics from all files
        const diagnosticsByFile = vscode.languages.getDiagnostics();

        const aggregated = diagnosticsByFile.map(([uri, diags]) => {
            return {
                file: uri.fsPath,
                diagnostics: diags.map(diag => ({
                    severity: vscode.DiagnosticSeverity[diag.severity],
                    message: diag.message,
                    source: diag.source
                }))
            };
        });

        // Output aggregated diagnostics to the output channel
        outputChannel.appendLine("Aggregated Diagnostics:");
        outputChannel.appendLine(JSON.stringify(aggregated, null, 2));
        outputChannel.show();

        vscode.window.showInformationMessage("Diagnostics aggregated to output channel.");
    });

    context.subscriptions.push(disposable);
}

export function deactivate() {}