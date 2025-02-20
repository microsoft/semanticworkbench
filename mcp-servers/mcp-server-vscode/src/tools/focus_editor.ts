import * as vscode from 'vscode';

export const focusEditorTool = async ({
    filePath,
    line = 0,
    column = 0,
    startLine,
    startColumn,
    endLine,
    endColumn,
}: {
    filePath: string;
    line?: number;
    column?: number;
    startLine?: number;
    startColumn?: number;
    endLine?: number;
    endColumn?: number;
}): Promise<{
    success: boolean;
    content: { type: 'text'; text: string }[];
}> => {
    const uri = vscode.Uri.file(filePath);
    const document = await vscode.workspace.openTextDocument(uri); // Open the document
    const editor = await vscode.window.showTextDocument(document); // Show it in the editor

    // Highlight range if all range parameters are provided
    if (
        typeof startLine === 'number' &&
        typeof startColumn === 'number' &&
        typeof endLine === 'number' &&
        typeof endColumn === 'number' &&
        // Ensure that a valid range is provided by checking that the start and end are not both zeros
        (startLine !== 0 || startColumn !== 0 || endLine !== 0 || endColumn !== 0)
    ) {
        const start = new vscode.Position(startLine, startColumn);
        const end = new vscode.Position(endLine, endColumn);
        editor.selection = new vscode.Selection(start, end);
        editor.revealRange(new vscode.Range(start, end), vscode.TextEditorRevealType.InCenter);
        return {
            success: true,
            content: [
                {
                    type: 'text' as const,
                    text: `Focused file: ${filePath} with highlighted range from line ${startLine}, column ${startColumn} to line ${endLine}, column ${endColumn}`,
                },
            ],
        };
    } else {
        // Move the cursor to the specified position
        const position = new vscode.Position(line, column);
        editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
        editor.selection = new vscode.Selection(position, position);

        return {
            success: true,
            content: [
                {
                    type: 'text' as const,
                    text: `Focused file: ${filePath} at line ${line}, column ${column}`,
                },
            ],
        };
    }
};
