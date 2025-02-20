import * as vscode from 'vscode';
import { focusEditorTool } from './focus_editor';

export async function searchSymbolTool({
    query,
    useDefinition = true,
    maxResults = 50,
    openFile = false, // Optional: Open files after search
}: {
    query: string;
    useDefinition?: boolean;
    maxResults?: number;
    openFile?: boolean;
}) {
    const results: {
        definition: {
            file: string;
            startLine: number;
            startColumn: number;
            endLine: number;
            endColumn: number;
            snippet: string;
        } | null;
        globalSearch: Array<{ file: string; line: number; snippet: string }>;
    } = { definition: null, globalSearch: [] };

    // Try "Go to Definition"
    if (useDefinition && vscode.window.activeTextEditor) {
        const editor = vscode.window.activeTextEditor;
        const position = editor.selection.active;
        const uri = editor.document.uri;

        const definitionResults = await vscode.commands.executeCommand<vscode.Location[]>(
            'vscode.executeDefinitionProvider',
            uri,
            position,
        );

        if (definitionResults && definitionResults.length > 0) {
            const def = definitionResults[0];
            results.definition = {
                file: def.uri.fsPath,
                startLine: def.range.start.line,
                startColumn: def.range.start.character,
                endLine: def.range.end.line,
                endColumn: def.range.end.character,
                snippet: def.range.start.line === def.range.end.line ? editor.document.getText(def.range) : '',
            };

            // Reuse `focusEditorTool` if applicable
            if (openFile) {
                await focusEditorTool({
                    filePath: def.uri.fsPath,
                    startLine: def.range.start.line,
                    startColumn: def.range.start.character,
                    endLine: def.range.end.line,
                    endColumn: def.range.end.character,
                });
            }
        }
    }

    // Perform a global text search
    const globalSearchResults: Array<any> = [];
    await vscode.commands.executeCommand<{ uri: vscode.Uri; ranges: vscode.Range[]; preview: { text: string } }[]>(
        'vscode.executeWorkspaceSymbolProvider',
        query,
        ({ uri, ranges, preview }: { uri: vscode.Uri; ranges: vscode.Range[]; preview: { text: string } }) => {
            const match = {
                file: uri.fsPath,
                line: ranges[0].start.line,
                snippet: preview.text.trim(),
            };

            if (globalSearchResults.length < maxResults) {
                globalSearchResults.push({
                    file: match.file, // Correct the key to 'file'
                    line: match.line, // Correct key/logic
                    snippet: match.snippet, // Correct key/logic
                });
            }
        },
    );

    results.globalSearch = globalSearchResults;

    // Open the first global search result if requested
    if (openFile && globalSearchResults.length > 0) {
        const firstMatch = globalSearchResults[0];
        await focusEditorTool({ filePath: firstMatch.file, line: firstMatch.line, column: 0 });
    }

    return results;
}
