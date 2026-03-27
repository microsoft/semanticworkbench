import * as vscode from 'vscode';
interface CommandRecord {
    command: string;
    output: string;
}
export declare const initTerminalOutputCapture: (context: vscode.ExtensionContext) => void;
export declare const getCommandHistory: (name: string) => CommandRecord[] | undefined;
export {};
