export declare function searchSymbolTool({ query, useDefinition, maxResults, openFile, }: {
    query: string;
    useDefinition?: boolean;
    maxResults?: number;
    openFile?: boolean;
}): Promise<{
    definition: {
        file: string;
        startLine: number;
        startColumn: number;
        endLine: number;
        endColumn: number;
        snippet: string;
    } | null;
    globalSearch: Array<{
        file: string;
        line: number;
        snippet: string;
    }>;
}>;
