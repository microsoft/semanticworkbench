export declare const focusEditorTool: ({ filePath, line, column, startLine, startColumn, endLine, endColumn, }: {
    filePath: string;
    line?: number;
    column?: number;
    startLine?: number;
    startColumn?: number;
    endLine?: number;
    endColumn?: number;
}) => Promise<{
    success: boolean;
    content: {
        type: "text";
        text: string;
    }[];
}>;
