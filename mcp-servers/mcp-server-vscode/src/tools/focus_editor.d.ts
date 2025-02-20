export declare function focusEditorTool({ filePath, line, column, }: {
    filePath: string;
    line?: number;
    column?: number;
}): Promise<{
    success: boolean;
    content: {
        type: "text";
        text: string;
    }[];
}>;
