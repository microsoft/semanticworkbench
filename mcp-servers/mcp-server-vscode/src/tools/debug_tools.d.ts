import * as vscode from 'vscode';
import { z } from 'zod';
interface BreakpointHitInfo {
    sessionId: string;
    sessionName: string;
    threadId: number;
    reason: string;
    frameId?: number;
    filePath?: string;
    line?: number;
    exceptionInfo?: {
        description: string;
        details: string;
    };
}
export declare const breakpointEventEmitter: vscode.EventEmitter<BreakpointHitInfo>;
export declare const onBreakpointHit: vscode.Event<BreakpointHitInfo>;
export declare const listDebugSessions: () => {
    content: {
        type: string;
        json: {
            sessions: {
                id: string;
                name: string;
                configuration: vscode.DebugConfiguration;
            }[];
        };
    }[];
    isError: boolean;
};
export declare const listDebugSessionsSchema: z.ZodObject<{}, "strip", z.ZodTypeAny, {}, {}>;
export declare const startDebugSession: (params: {
    workspaceFolder: string;
    configuration: {
        type: string;
        request: string;
        name: string;
        [key: string]: any;
    };
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const startDebugSessionSchema: z.ZodObject<{
    workspaceFolder: z.ZodString;
    configuration: z.ZodObject<{
        type: z.ZodString;
        request: z.ZodString;
        name: z.ZodString;
    }, "passthrough", z.ZodTypeAny, z.objectOutputType<{
        type: z.ZodString;
        request: z.ZodString;
        name: z.ZodString;
    }, z.ZodTypeAny, "passthrough">, z.objectInputType<{
        type: z.ZodString;
        request: z.ZodString;
        name: z.ZodString;
    }, z.ZodTypeAny, "passthrough">>;
}, "strip", z.ZodTypeAny, {
    workspaceFolder: string;
    configuration: {
        name: string;
        type: string;
        request: string;
    } & {
        [k: string]: unknown;
    };
}, {
    workspaceFolder: string;
    configuration: {
        name: string;
        type: string;
        request: string;
    } & {
        [k: string]: unknown;
    };
}>;
export declare const stopDebugSession: (params: {
    sessionName: string;
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const stopDebugSessionSchema: z.ZodObject<{
    sessionName: z.ZodString;
}, "strip", z.ZodTypeAny, {
    sessionName: string;
}, {
    sessionName: string;
}>;
export declare const setBreakpoint: (params: {
    filePath: string;
    line: number;
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const setBreakpointSchema: z.ZodObject<{
    filePath: z.ZodString;
    line: z.ZodNumber;
}, "strip", z.ZodTypeAny, {
    filePath: string;
    line: number;
}, {
    filePath: string;
    line: number;
}>;
export declare const getCallStack: (params: {
    sessionName?: string;
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
} | {
    content: {
        type: string;
        json: {
            callStacks: ({
                sessionId: string;
                sessionName: string;
                threads: any[];
                error?: undefined;
            } | {
                sessionId: string;
                sessionName: string;
                error: string;
                threads?: undefined;
            })[];
        };
    }[];
    isError: boolean;
}>;
export declare const getCallStackSchema: z.ZodObject<{
    sessionName: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    sessionName?: string | undefined;
}, {
    sessionName?: string | undefined;
}>;
export declare const resumeDebugSession: (params: {
    sessionId: string;
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
}>;
export declare const resumeDebugSessionSchema: z.ZodObject<{
    sessionId: z.ZodString;
}, "strip", z.ZodTypeAny, {
    sessionId: string;
}, {
    sessionId: string;
}>;
export declare const getStackFrameVariables: (params: {
    sessionId: string;
    frameId: number;
    threadId: number;
    filter?: string;
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
} | {
    content: {
        type: string;
        json: {
            sessionId: string;
            frameId: number;
            threadId: number;
            variablesByScope: any[];
            filter: string | undefined;
        };
    }[];
    isError: boolean;
}>;
export declare const getStackFrameVariablesSchema: z.ZodObject<{
    sessionId: z.ZodString;
    frameId: z.ZodNumber;
    threadId: z.ZodNumber;
    filter: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    sessionId: string;
    frameId: number;
    threadId: number;
    filter?: string | undefined;
}, {
    sessionId: string;
    frameId: number;
    threadId: number;
    filter?: string | undefined;
}>;
export declare const waitForBreakpointHit: (params: {
    sessionId?: string;
    sessionName?: string;
    timeout?: number;
}) => Promise<{
    content: {
        type: string;
        text: string;
    }[];
    isError: boolean;
} | {
    content: {
        type: string;
        json: {
            sessionId: string;
            sessionName: string;
            threadId: number;
            reason: string;
            frameId?: number;
            filePath?: string;
            line?: number;
        };
    }[];
    isError: boolean;
}>;
export declare const waitForBreakpointHitSchema: z.ZodEffects<z.ZodObject<{
    sessionId: z.ZodOptional<z.ZodString>;
    sessionName: z.ZodOptional<z.ZodString>;
    timeout: z.ZodOptional<z.ZodNumber>;
}, "strip", z.ZodTypeAny, {
    sessionName?: string | undefined;
    sessionId?: string | undefined;
    timeout?: number | undefined;
}, {
    sessionName?: string | undefined;
    sessionId?: string | undefined;
    timeout?: number | undefined;
}>, {
    sessionName?: string | undefined;
    sessionId?: string | undefined;
    timeout?: number | undefined;
}, {
    sessionName?: string | undefined;
    sessionId?: string | undefined;
    timeout?: number | undefined;
}>;
export declare const subscribeToBreakpointEvents: (params: {
    sessionId?: string;
    sessionName?: string;
}) => Promise<{
    content: {
        type: string;
        json: {
            subscriptionId: string;
            message: string;
        };
    }[];
    isError: boolean;
    _meta: {
        subscriptionId: string;
        type: string;
        filter: {
            sessionId: string | undefined;
            sessionName: string | undefined;
        };
    };
}>;
export declare const subscribeToBreakpointEventsSchema: z.ZodObject<{
    sessionId: z.ZodOptional<z.ZodString>;
    sessionName: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    sessionName?: string | undefined;
    sessionId?: string | undefined;
}, {
    sessionName?: string | undefined;
    sessionId?: string | undefined;
}>;
export declare const listBreakpoints: (params?: {
    filePath?: string;
}) => {
    content: {
        type: string;
        json: {
            breakpoints: ({
                id: string;
                enabled: boolean;
                condition: string | undefined;
                hitCondition: string | undefined;
                logMessage: string | undefined;
                file: {
                    path: string;
                    name: string;
                };
                location: {
                    line: number;
                    column: number;
                };
                functionName?: undefined;
                type?: undefined;
            } | {
                id: string;
                enabled: boolean;
                functionName: string;
                condition: string | undefined;
                hitCondition: string | undefined;
                logMessage: string | undefined;
                file?: undefined;
                location?: undefined;
                type?: undefined;
            } | {
                id: string;
                enabled: boolean;
                type: string;
                condition?: undefined;
                hitCondition?: undefined;
                logMessage?: undefined;
                file?: undefined;
                location?: undefined;
                functionName?: undefined;
            })[];
            count: number;
            filter: {
                filePath: string;
            } | undefined;
        };
    }[];
    isError: boolean;
};
export declare const listBreakpointsSchema: z.ZodObject<{
    filePath: z.ZodOptional<z.ZodString>;
}, "strip", z.ZodTypeAny, {
    filePath?: string | undefined;
}, {
    filePath?: string | undefined;
}>;
export {};
