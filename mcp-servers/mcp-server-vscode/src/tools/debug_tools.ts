import * as path from 'path';
import * as vscode from 'vscode';
import { z } from 'zod';

// Create an output channel for debugging
const outputChannel = vscode.window.createOutputChannel('Debug Tools');

/** Maintain a list of active debug sessions. */
const activeSessions: vscode.DebugSession[] = [];

/** Store breakpoint hit information for notification */
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

/** Event emitter for breakpoint hit notifications */
export const breakpointEventEmitter = new vscode.EventEmitter<BreakpointHitInfo>();
export const onBreakpointHit = breakpointEventEmitter.event;

// Track new debug sessions as they start.
vscode.debug.onDidStartDebugSession((session) => {
    activeSessions.push(session);
    outputChannel.appendLine(`Debug session started: ${session.name} (ID: ${session.id})`);
    outputChannel.appendLine(`Active sessions: ${activeSessions.length}`);
});

// Remove debug sessions as they terminate.
vscode.debug.onDidTerminateDebugSession((session) => {
    const index = activeSessions.indexOf(session);
    if (index >= 0) {
        activeSessions.splice(index, 1);
        outputChannel.appendLine(`Debug session terminated: ${session.name} (ID: ${session.id})`);
        outputChannel.appendLine(`Active sessions: ${activeSessions.length}`);
    }
});

vscode.debug.onDidChangeActiveDebugSession((session) => {
    outputChannel.appendLine(`Active debug session changed: ${session ? session.name : 'None'}`);
});
vscode.debug.registerDebugAdapterTrackerFactory('*', {
    createDebugAdapterTracker: (session: vscode.DebugSession): vscode.ProviderResult<vscode.DebugAdapterTracker> => {
        // Create a class that implements the DebugAdapterTracker interface
        class DebugAdapterTrackerImpl implements vscode.DebugAdapterTracker {
            onWillStartSession?(): void {
                outputChannel.appendLine(`Debug session starting: ${session.name}`);
            }

            onWillReceiveMessage?(message: any): void {
                // Optional: Log messages being received by the debug adapter
                outputChannel.appendLine(`Message received by debug adapter: ${JSON.stringify(message)}`);
            }

            onDidSendMessage(message: any): void {
                // Log all messages sent from the debug adapter to VS Code
                if (message.type === 'event') {
                    const event = message;
                    // The 'stopped' event is fired when execution stops (e.g., at a breakpoint or exception)
                    if (event.event === 'stopped') {
                        const body = event.body;
                        // Process any stop event - including breakpoints, exceptions, and other stops
                        const validReasons = ['breakpoint', 'step', 'pause', 'exception', 'assertion', 'entry'];

                        if (validReasons.includes(body.reason)) {
                            // Use existing getCallStack function to get thread and stack information
                            (async () => {
                                try {
                                    // Collect exception details if this is an exception
                                    let exceptionDetails = undefined;
                                    if (body.reason === 'exception' && body.description) {
                                        exceptionDetails = {
                                            description: body.description || 'Unknown exception',
                                            details: body.text || 'No additional details available',
                                        };
                                    }

                                    // Get call stack information for the session
                                    const callStackResult = await getCallStack({ sessionName: session.name });

                                    if (callStackResult.isError) {
                                        // If we couldn't get call stack, emit basic event
                                        breakpointEventEmitter.fire({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                            exceptionInfo: exceptionDetails,
                                        });
                                        return;
                                    }
                                    if (!('json' in callStackResult.content[0])) {
                                        // If the content is not JSON, emit basic event
                                        breakpointEventEmitter.fire({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                            exceptionInfo: exceptionDetails,
                                        });
                                        return;
                                    }
                                    // Extract call stack data from the result
                                    const callStackData = callStackResult.content[0].json?.callStacks[0];
                                    if (!('threads' in callStackData)) {
                                        // If threads are not present, emit basic event
                                        breakpointEventEmitter.fire({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                            exceptionInfo: exceptionDetails,
                                        });
                                        return;
                                    }
                                    // If threads are present, find the one that matches the threadId
                                    if (!Array.isArray(callStackData.threads)) {
                                        breakpointEventEmitter.fire({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                            exceptionInfo: exceptionDetails,
                                        });
                                        return;
                                    }
                                    // Find the thread that triggered the event
                                    const threadData = callStackData.threads.find(
                                        (t: any) => t.threadId === body.threadId,
                                    );

                                    if (!threadData || !threadData.stackFrames || threadData.stackFrames.length === 0) {
                                        // If thread or stack frames not found, emit basic event
                                        breakpointEventEmitter.fire({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                            exceptionInfo: exceptionDetails,
                                        });
                                        return;
                                    }

                                    // Get the top stack frame
                                    const topFrame = threadData.stackFrames[0];

                                    // Emit breakpoint/exception hit event with stack frame information
                                    const eventData = {
                                        sessionId: session.id,
                                        sessionName: session.name,
                                        threadId: body.threadId,
                                        reason: body.reason,
                                        frameId: topFrame.id,
                                        filePath: topFrame.source?.path,
                                        line: topFrame.line,
                                        exceptionInfo: exceptionDetails,
                                    };

                                    outputChannel.appendLine(`Firing breakpoint event: ${JSON.stringify(eventData)}`);
                                    breakpointEventEmitter.fire(eventData);
                                } catch (error) {
                                    console.error('Error processing debug event:', error);
                                    // Still emit event with basic info
                                    const exceptionDetails =
                                        body.reason === 'exception'
                                            ? {
                                                  description: body.description || 'Unknown exception',
                                                  details: body.text || 'No details available',
                                              }
                                            : undefined;

                                    breakpointEventEmitter.fire({
                                        sessionId: session.id,
                                        sessionName: session.name,
                                        threadId: body.threadId,
                                        reason: body.reason,
                                        exceptionInfo: exceptionDetails,
                                    });
                                }
                            })();
                        }
                    }
                }
                outputChannel.appendLine(`Message from debug adapter: ${JSON.stringify(message)}`);
            }

            onWillSendMessage(message: any): void {
                // Log all messages sent to the debug adapter
                outputChannel.appendLine(`Message sent to debug adapter: ${JSON.stringify(message)}`);
            }

            onDidReceiveMessage(message: any): void {
                // Log all messages received from the debug adapter
                outputChannel.appendLine(`Message received from debug adapter: ${JSON.stringify(message)}`);
            }

            onError?(error: Error): void {
                outputChannel.appendLine(`Debug adapter error: ${error.message}`);
            }

            onExit?(code: number | undefined, signal: string | undefined): void {
                outputChannel.appendLine(`Debug adapter exited: code=${code}, signal=${signal}`);
            }
        }

        return new DebugAdapterTrackerImpl();
    },
});
// Listen for breakpoint hit events

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
        const breakpoint = new vscode.SourceBreakpoint(new vscode.Location(fileUri, new vscode.Position(line - 1, 0)));

        // Add the breakpoint - note that addBreakpoints returns void, not an array
        vscode.debug.addBreakpoints([breakpoint]);

        // Check if the breakpoint was successfully added by verifying it exists in VS Code's breakpoints
        const breakpoints = vscode.debug.breakpoints;
        const breakpointAdded = breakpoints.some((bp) => {
            if (bp instanceof vscode.SourceBreakpoint) {
                const loc = bp.location;
                return loc.uri.fsPath === fileUri.fsPath && loc.range.start.line === line - 1;
            }
            return false;
        });

        if (!breakpointAdded) {
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
                                        source: frame.source
                                            ? {
                                                  name: frame.source.name,
                                                  path: frame.source.path,
                                              }
                                            : undefined,
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
                        }),
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
            }),
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
    sessionName: z
        .string()
        .optional()
        .describe(
            'The name of the debug session to get call stack for. If not provided, returns call stacks for all active sessions.',
        ),
});

/**
 * Resume execution of a debug session that has been paused (e.g., by a breakpoint).
 *
 * @param params - Object containing the sessionId of the debug session to resume.
 */
export const resumeDebugSession = async (params: { sessionId: string }) => {
    const { sessionId } = params;

    // Find the session with the given ID
    const session = activeSessions.find((s) => s.id === sessionId);
    if (!session) {
        return {
            content: [
                {
                    type: 'text',
                    text: `No debug session found with ID '${sessionId}'.`,
                },
            ],
            isError: true,
        };
    }

    try {
        // Send the continue request to the debug adapter
        await session.customRequest('continue', { threadId: 0 }); // 0 means all threads

        return {
            content: [
                {
                    type: 'text',
                    text: `Resumed debug session '${session.name}'.`,
                },
            ],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error resuming debug session: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
};

// Zod schema for validating resume_debug_session parameters.
export const resumeDebugSessionSchema = z.object({
    sessionId: z.string().describe('The ID of the debug session to resume.'),
});

/**
 * Get variables from a specific stack frame.
 *
 * @param params - Object containing sessionId, frameId, threadId, and optional filter to get variables from.
 */
export const getStackFrameVariables = async (params: {
    sessionId: string;
    frameId: number;
    threadId: number;
    filter?: string;
}) => {
    const { sessionId, frameId, threadId, filter } = params;

    // Find the session with the given ID
    const session = activeSessions.find((s) => s.id === sessionId);
    if (!session) {
        return {
            content: [
                {
                    type: 'text',
                    text: `No debug session found with ID '${sessionId}'.`,
                },
            ],
            isError: true,
        };
    }

    try {
        // First, get the scopes for the stack frame
        const scopes = await session.customRequest('scopes', { frameId });

        // Then, get variables for each scope
        const variablesByScope = await Promise.all(
            scopes.scopes.map(async (scope: { name: string; variablesReference: number }) => {
                if (scope.variablesReference === 0) {
                    return {
                        scopeName: scope.name,
                        variables: [],
                    };
                }

                const response = await session.customRequest('variables', {
                    variablesReference: scope.variablesReference,
                });

                // Apply filter if provided
                let filteredVariables = response.variables;
                if (filter) {
                    const filterRegex = new RegExp(filter, 'i'); // Case insensitive match
                    filteredVariables = response.variables.filter((variable: { name: string }) =>
                        filterRegex.test(variable.name),
                    );
                }

                return {
                    scopeName: scope.name,
                    variables: filteredVariables,
                };
            }),
        );

        return {
            content: [
                {
                    type: 'json',
                    json: {
                        sessionId,
                        frameId,
                        threadId,
                        variablesByScope,
                        filter: filter || undefined,
                    },
                },
            ],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error getting variables: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
};

// Zod schema for validating get_stack_frame_variables parameters.
export const getStackFrameVariablesSchema = z.object({
    sessionId: z.string().describe('The ID of the debug session.'),
    frameId: z.number().describe('The ID of the stack frame to get variables from.'),
    threadId: z.number().describe('The ID of the thread containing the stack frame.'),
    filter: z.string().optional().describe('Optional filter pattern to match variable names.'),
});

/**
 * Wait for a breakpoint to be hit in a debug session.
 *
 * @param params - Object containing sessionId or sessionName to identify the debug session, and optional timeout.
 */
export const waitForBreakpointHit = async (params: { sessionId?: string; sessionName?: string; timeout?: number }) => {
    const { sessionId, sessionName, timeout = 30000 } = params; // Default timeout: 30 seconds

    // Find the targeted debug session(s)
    let targetSessions: vscode.DebugSession[] = [];

    if (sessionId) {
        const session = activeSessions.find((s) => s.id === sessionId);
        if (session) {
            targetSessions = [session];
        }
    } else if (sessionName) {
        targetSessions = activeSessions.filter((s) => s.name === sessionName);
    } else {
        targetSessions = [...activeSessions]; // All active sessions if neither ID nor name provided
    }

    if (targetSessions.length === 0) {
        return {
            content: [
                {
                    type: 'text',
                    text: `No matching debug sessions found.`,
                },
            ],
            isError: true,
        };
    }

    try {
        // Create a promise that resolves when a breakpoint is hit
        const breakpointHitPromise = new Promise<{
            sessionId: string;
            sessionName: string;
            threadId: number;
            reason: string;
            frameId?: number;
            filePath?: string;
            line?: number;
        }>((resolve, reject) => {
            // Listen for the 'stopped' event from the debug adapter
            const sessionStoppedListener = vscode.debug.onDidReceiveDebugSessionCustomEvent((event) => {
                // The 'stopped' event is fired when execution stops (e.g., at a breakpoint)
                if (event.event === 'stopped' && targetSessions.some((s) => s.id === event.session.id)) {
                    const session = event.session;
                    const body = event.body;

                    if (body.reason === 'breakpoint' || body.reason === 'step' || body.reason === 'pause') {
                        // Get the first stack frame to provide the frameId
                        (async () => {
                            try {
                                const threadsResponse = await Promise.resolve(session.customRequest('threads'));
                                const thread = threadsResponse.threads.find((t: any) => t.id === body.threadId);

                                if (thread) {
                                    try {
                                        const stackTrace = await Promise.resolve(
                                            session.customRequest('stackTrace', { threadId: body.threadId }),
                                        );

                                        const frameId =
                                            stackTrace.stackFrames.length > 0
                                                ? stackTrace.stackFrames[0].id
                                                : undefined;
                                        const filePath =
                                            stackTrace.stackFrames.length > 0 && stackTrace.stackFrames[0].source
                                                ? stackTrace.stackFrames[0].source.path
                                                : undefined;
                                        const line =
                                            stackTrace.stackFrames.length > 0
                                                ? stackTrace.stackFrames[0].line
                                                : undefined;

                                        // Clean up the listener before resolving
                                        sessionStoppedListener.dispose();

                                        resolve({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                            frameId,
                                            filePath,
                                            line,
                                        });
                                    } catch (error) {
                                        // Clean up the listener before resolving
                                        sessionStoppedListener.dispose();

                                        // Still resolve, but without frameId
                                        resolve({
                                            sessionId: session.id,
                                            sessionName: session.name,
                                            threadId: body.threadId,
                                            reason: body.reason,
                                        });
                                    }
                                } else {
                                    // Clean up the listener before resolving
                                    sessionStoppedListener.dispose();

                                    resolve({
                                        sessionId: session.id,
                                        sessionName: session.name,
                                        threadId: body.threadId,
                                        reason: body.reason,
                                    });
                                }
                            } catch (error) {
                                // Clean up the listener before resolving
                                sessionStoppedListener.dispose();

                                // Still resolve with basic info
                                resolve({
                                    sessionId: session.id,
                                    sessionName: session.name,
                                    threadId: body.threadId,
                                    reason: body.reason,
                                });
                            }
                        })();
                    }
                }
            });

            // Set a timeout to prevent blocking indefinitely
            setTimeout(() => {
                sessionStoppedListener.dispose();
                reject(new Error(`Timed out waiting for breakpoint to be hit (${timeout}ms).`));
            }, timeout);
        });

        // Wait for the breakpoint to be hit or timeout
        const result = await breakpointHitPromise;

        return {
            content: [
                {
                    type: 'json',
                    json: result,
                },
            ],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `Error waiting for breakpoint: ${error instanceof Error ? error.message : String(error)}`,
                },
            ],
            isError: true,
        };
    }
};

/**
 * Provides a way for MCP clients to subscribe to breakpoint hit events.
 * This tool returns immediately with a subscription ID, and the MCP client
 * will receive notifications when breakpoints are hit.
 *
 * @param params - Object containing an optional filter for the debug sessions to monitor.
 */
export const subscribeToBreakpointEvents = async (params: { sessionId?: string; sessionName?: string }) => {
    const { sessionId, sessionName } = params;

    // Generate a unique subscription ID
    const subscriptionId = `breakpoint-subscription-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

    // Return immediately with subscription info
    return {
        content: [
            {
                type: 'json',
                json: {
                    subscriptionId,
                    message:
                        'Subscribed to breakpoint events. You will receive notifications when breakpoints are hit.',
                },
            },
        ],
        isError: false,
        // Special metadata to indicate this is a subscription
        _meta: {
            subscriptionId,
            type: 'breakpoint-events',
            filter: { sessionId, sessionName },
        },
    };
};

// Zod schema for validating subscribe_to_breakpoint_events parameters.
export const subscribeToBreakpointEventsSchema = z.object({
    sessionId: z.string().optional().describe('Filter events to this specific debug session ID.'),
    sessionName: z.string().optional().describe('Filter events to debug sessions with this name.'),
});

/**
 * Get a list of all currently set breakpoints in the workspace.
 *
 * @param params - Optional object containing a file path filter.
 */
export const listBreakpoints = (params: { filePath?: string } = {}) => {
    const { filePath } = params;

    // Get all breakpoints
    const allBreakpoints = vscode.debug.breakpoints;

    // Filter breakpoints by file path if provided
    const filteredBreakpoints = filePath
        ? allBreakpoints.filter((bp) => {
              if (bp instanceof vscode.SourceBreakpoint) {
                  return bp.location.uri.fsPath === filePath;
              }
              return false;
          })
        : allBreakpoints;

    // Transform breakpoints into a more readable format
    const breakpointData = filteredBreakpoints.map((bp) => {
        if (bp instanceof vscode.SourceBreakpoint) {
            const location = bp.location;
            return {
                id: bp.id,
                enabled: bp.enabled,
                condition: bp.condition,
                hitCondition: bp.hitCondition,
                logMessage: bp.logMessage,
                file: {
                    path: location.uri.fsPath,
                    name: path.basename(location.uri.fsPath),
                },
                location: {
                    line: location.range.start.line + 1, // Convert to 1-based for user display
                    column: location.range.start.character + 1,
                },
            };
        } else if (bp instanceof vscode.FunctionBreakpoint) {
            return {
                id: bp.id,
                enabled: bp.enabled,
                functionName: bp.functionName,
                condition: bp.condition,
                hitCondition: bp.hitCondition,
                logMessage: bp.logMessage,
            };
        } else {
            return {
                id: bp.id,
                enabled: bp.enabled,
                type: 'unknown',
            };
        }
    });

    return {
        content: [
            {
                type: 'json',
                json: {
                    breakpoints: breakpointData,
                    count: breakpointData.length,
                    filter: filePath ? { filePath } : undefined,
                },
            },
        ],
        isError: false,
    };
};

// Zod schema for validating list_breakpoints parameters.
export const listBreakpointsSchema = z.object({
    filePath: z.string().optional().describe('Optional file path to filter breakpoints by file.'),
});
