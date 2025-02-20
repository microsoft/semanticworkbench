import * as vscode from "vscode";

export async function focusEditorTool({
  filePath,
  line = 0,
  column = 0,
}: {
  filePath: string;
  line?: number;
  column?: number;
}) {
  const uri = vscode.Uri.file(filePath);
  const document = await vscode.workspace.openTextDocument(uri); // Open the document
  const editor = await vscode.window.showTextDocument(document); // Show it in the editor

  // Move the cursor to the specified position
  const position = new vscode.Position(line, column);
  editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
  editor.selection = new vscode.Selection(position, position);

  return {
    success: true,
    content: [
      {
        type: "text" as const,
        text: `Focused file: ${filePath} at line ${line}, column ${column}`,
      },
    ],
  };
}