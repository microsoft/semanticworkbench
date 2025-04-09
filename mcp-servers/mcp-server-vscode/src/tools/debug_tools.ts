import * as path from 'path';
import * as vscode from 'vscode';
import { z } from 'zod';

/** Maintain a list of active debug sessions. */
const activeSessions: vscode.DebugSession[] = [];

// Track new debug sessions as they start.
vscode.debug.onDidStartDebugSession((session) => {
    activeSessions.push(session);
});

// Remove debug sessions as they terminate.
vscode.debug.onDidTerminateDebugSession((session) => {
    const index = activeSessions.indexOf(session);
    if (index >= 0) {
        activeSessions.splice(index, 1);
    }
});

/**
 * List all active debug sessions in the workspace.
 *
 * Exposes debug session information, including each session's ID, name, and associated launch configuration.
 */
export const listDebugSessions = () => {
    // Retrieve all active debug sessions using the activeSessions array.
    const sessions = activeSessions.map((session: vscode.DebugSession) => ({
        id: session.id,
        name: session.name,
        configuration: session.configuration,
    }));

    // Return session list
    return {
        content: [
            {
                type: 'json',
                json: { sessions },
            },
        ],
        isError: false,
    };
};

// Zod schema for validating tool parameters (none for this tool).
export const listDebugSessionsSchema = z.object({});

/**
 * Start a new debug session using the provided configuration.
 *
 * @param params - Object containing workspaceFolder and configuration details.
 */
export const startDebugSession = async (params: {
    workspaceFolder: string;
    configuration: { type: string; request: string; name: string; [key: string]: any };
}) => {
    const { workspaceFolder, configuration } = params;
    // Ensure that workspace folders exist and are accessible.
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (!workspaceFolders || workspaceFolders.length === 0) {
        throw new Error('No workspace folders are currently open.');
    }

    const folder = workspaceFolders.find((f) => f.uri?.fsPath === workspaceFolder);
    if (!folder) {
        throw new Error(`Workspace folder '${workspaceFolder}' not found.`);
    }

    const success = await vscode.debug.startDebugging(folder, configuration);

    if (!success) {
        throw new Error(`Failed to start debug session '${configuration.name}'.`);
    }

    return {
        content: [{ type: 'text', text: `Debug session '${configuration.name}' started successfully.` }],
        isError: false,
    };
};

// Zod schema for validating start_debug_session parameters.
export const startDebugSessionSchema = z.object({
    workspaceFolder: z.string().describe('The workspace folder where the debug session should start.'),
    configuration: z
        .object({
            type: z.string().describe("Type of the debugger (e.g., 'node', 'python', etc.)."),
            request: z.string().describe("Type of debug request (e.g., 'launch' or 'attach')."),
            name: z.string().describe('Name of the debug session.'),
        })
        .passthrough()
        .describe('The debug configuration object.'),
});

/**
 * Stop debug sessions that match the provided session name.
 *
 * @param params - Object containing the sessionName to stop.
 */
export const stopDebugSession = async (params: { sessionName: string }) => {
    const { sessionName } = params;
    // Filter active sessions to find matching sessions.
    const matchingSessions = activeSessions.filter((session: vscode.DebugSession) => session.name === sessionName);

    if (matchingSessions.length === 0) {
        return {
            content: [
                {
                    type: 'text',
                    text: `No debug session(s) found with name '${sessionName}'.`,
                },
            ],
            isError: true,
        };
    }

    // Stop each matching debug session.
    for (const session of matchingSessions) {
        await vscode.debug.stopDebugging(session);
    }

    return {
        content: [
            {
                type: 'text',
                text: `Stopped debug session(s) with name '${sessionName}'.`,
            },
        ],
        isError: false,
    };
};

// Zod schema for validating stop_debug_session parameters.
export const stopDebugSessionSchema = z.object({
    sessionName: z.string().describe('The name of the debug session(s) to stop.'),
});

/**
 * Set a breakpoint at a specific line in a file.
 *
 * @param params - Object containing filePath and line number for the breakpoint.
 */
export const setBreakpoint = async (params: { filePath: string; line: number }) => {
    const { filePath, line } = params;

    try {
        // Create a URI from the file path
        const fileUri = vscode.Uri.file(filePath);

        // Check if the file exists
        try {
            await vscode.workspace.fs.stat(fileUri);
        } catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `File not found: ${filePath}`,
                    },
                ],
                isError: true,
            };
        }

        // Create a new breakpoint
        const breakpoint = new vscode.SourceBreakpoint(
            new vscode.Location(fileUri, new vscode.Position(line - 1, 0))
        );

        // Add the breakpoint
        const added = vscode.debug.addBreakpoints([breakpoint]);

        if (added.length === 0) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Failed to set breakpoint at line ${line} in ${path.basename(filePath)}`,
                    },
                ],
                isError: true,
            };
        }

        return {
            content: [
                {
                    type: 'text',
                    text: `Breakpoint set at line ${line} in ${path.basename(filePath)}`,
                },
            ],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error setting breakpoint: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
};

// Zod schema for validating set_breakpoint parameters.
export const setBreakpointSchema = z.object({
    filePath: z.string().describe('The absolute path to the file where the breakpoint should be set.'),
    line: z.number().int().min(1).describe('The line number where the breakpoint should be set (1-based).'),
});

/**
 * Get the current call stack information for an active debug session.
 *
 * @param params - Object containing the sessionName to get call stack for.
 */
export const getCallStack = async (params: { sessionName?: string }) => {
    const { sessionName } = params;

    // Get all active debug sessions or filter by name if provided
    let sessions = activeSessions;
    if (sessionName) {
        sessions = activeSessions.filter((session) => session.name === sessionName);
        if (sessions.length === 0) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `No debug session found with name '${sessionName}'.`,
                    },
                ],
                isError: true,
            };
        }
    }

    if (sessions.length === 0) {
        return {
            content: [
                {
                    type: 'text',
                    text: 'No active debug sessions found.',
                },
            ],
            isError: true,
        };
    }

    try {
        // Get call stack information for each session
        const callStacks = await Promise.all(
            sessions.map(async (session) => {
                try {
                    // Get all threads for the session
                    const threads = await session.customRequest('threads');

                    // Get stack traces for each thread
                    const stackTraces = await Promise.all(
                        threads.threads.map(async (thread: { id: number; name: string }) => {
                            try {
                                const stackTrace = await session.customRequest('stackTrace', {
                                    threadId: thread.id,
                                });

                                return {
                                    threadId: thread.id,
                                    threadName: thread.name,
                                    stackFrames: stackTrace.stackFrames.map((frame: any) => ({
                                        id: frame.id,
                                        name: frame.name,
                                        source: frame.source ? {
                                            name: frame.source.name,
                                            path: frame.source.path,
                                        } : undefined,
                                        line: frame.line,
                                        column: frame.column,
                                    })),
                                };
                            } catch (error) {
                                return {
                                    threadId: thread.id,
                                    threadName: thread.name,
                                    error: error instanceof Error ? error.message : String(error),
                                };
                            }
                        })
                    );

                    return {
                        sessionId: session.id,
                        sessionName: session.name,
                        threads: stackTraces,
                    };
                } catch (error) {
                    return {
                        sessionId: session.id,
                        sessionName: session.name,
                        error: error instanceof Error ? error.message : String(error),
                    };
                }
            })
        );

        return {
            content: [
                {
                    type: 'json',
                    json: { callStacks },
                },
            ],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error getting call stack: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
};

// Zod schema for validating get_call_stack parameters.
export const getCallStackSchema = z.object({
    sessionName: z.string().optional().describe('The name of the debug session to get call stack for. If not provided, returns call stacks for all active sessions.'),
});
