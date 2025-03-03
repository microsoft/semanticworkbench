import * as vscode from 'vscode';
declare global {
    var __VSCODE_MCP_SERVER_URL: string | undefined;
}
export declare const activate: (context: vscode.ExtensionContext) => Promise<void>;
export declare function deactivate(): void;
