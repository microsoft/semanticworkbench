import { z } from 'zod';
export declare const createTerminalSchema: z.ZodObject<{
    name: z.ZodOptional<z.ZodString>;
    cwd: z.ZodOptional<z.ZodString>;
    command: z.ZodOptional<z.ZodString>;
    show: z.ZodDefault<z.ZodBoolean>;
}, "strip", z.ZodTypeAny, {
    show: boolean;
    name?: string | undefined;
    cwd?: string | undefined;
    command?: string | undefined;
}, {
    name?: string | undefined;
    cwd?: string | undefined;
    command?: string | undefined;
    show?: boolean | undefined;
}>;
export declare const createTerminal: (params: z.infer<typeof createTerminalSchema>) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const listTerminalsSchema: z.ZodObject<{}, "strip", z.ZodTypeAny, {}, {}>;
export declare const listTerminals: () => {
    content: {
        type: string;
        json: {
            terminals: {
                index: number;
                name: string;
                processId: Thenable<number | undefined>;
            }[];
        };
    }[];
    isError: boolean;
};
export declare const sendTerminalTextSchema: z.ZodObject<{
    name: z.ZodString;
    text: z.ZodString;
    addNewLine: z.ZodDefault<z.ZodBoolean>;
}, "strip", z.ZodTypeAny, {
    text: string;
    name: string;
    addNewLine: boolean;
}, {
    text: string;
    name: string;
    addNewLine?: boolean | undefined;
}>;
export declare const sendTerminalText: (params: z.infer<typeof sendTerminalTextSchema>) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const closeTerminalSchema: z.ZodObject<{
    name: z.ZodString;
}, "strip", z.ZodTypeAny, {
    name: string;
}, {
    name: string;
}>;
export declare const getTerminalOutputSchema: z.ZodObject<{
    name: z.ZodString;
    commandIndex: z.ZodOptional<z.ZodNumber>;
    limit: z.ZodDefault<z.ZodNumber>;
}, "strip", z.ZodTypeAny, {
    name: string;
    limit: number;
    commandIndex?: number | undefined;
}, {
    name: string;
    commandIndex?: number | undefined;
    limit?: number | undefined;
}>;
export declare const getTerminalOutput: (params: z.infer<typeof getTerminalOutputSchema>) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const closeTerminal: (params: z.infer<typeof closeTerminalSchema>) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
