import * as vscode from 'vscode';
import { z } from 'zod';
import { activeSessions, outputChannel } from './common';

/**
 * Helper function to wait for a debug session to stop and gather debug information.
 * This is used by both startDebugSession and resumeDebugSession when waitForStop is true.
 *
 * @param params - Object containing session information and options for waiting.
 * @returns A response object with debug information or error details.
 */
async function waitForDebugSessionToStop(params: {
    sessionId?: string;
    sessionName?: string;
    actionType: 'started' | 'resumed';
    timeout?: number;
}) {
    const { sessionId, sessionName, actionType, timeout = 30000 } = params;

    try {
        // Import the functions we need
        const { waitForBreakpointHit } = await import('./events');
        const { getCallStack } = await import('./common');
        const { getStackFrameVariables } = await import('./inspection');

        // Find the session if we have a sessionId but not a sessionName
        let resolvedSessionName = sessionName;
        if (!resolvedSessionName && sessionId) {
            const session = activeSessions.find((s) => s.id === sessionId);
            if (session) {
                resolvedSessionName = session.name;
            }
        }

        outputChannel.appendLine(
            `Waiting for debug session ${resolvedSessionName || sessionId} to stop at a breakpoint`,
        );

        // Wait for the debug session to stop
        const stopResult = await waitForBreakpointHit({
            sessionId,
            sessionName: resolvedSessionName,
            timeout,
        });

        if (stopResult.isError) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Debug session ${resolvedSessionName || sessionId} ${actionType} successfully.`,
                    },
                    {
                        type: 'text',
                        text: `Warning: ${
                            'text' in stopResult.content[0]
                                ? stopResult.content[0].text
                                : 'Failed to wait for debug session to stop'
                        }`,
                    },
                ],
                isError: false,
            };
        }

        // Extract breakpoint hit information - now it's in text format
        const breakpointInfoText = stopResult.content[0].text;
        let breakpointInfo;
        try {
            breakpointInfo = JSON.parse(breakpointInfoText);
        } catch (e) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `Debug session ${
                            resolvedSessionName || sessionId
                        } ${actionType} successfully and stopped.`,
                    },
                    { type: 'text', text: 'Breakpoint hit, but failed to parse details.' },
                ],
                isError: false,
            };
        }

        // Get detailed call stack information
        const callStackResult = await getCallStack({ sessionName: resolvedSessionName || breakpointInfo.sessionName });
        let callStackData = null;
        if (!callStackResult.isError && 'json' in callStackResult.content[0]) {
            callStackData = callStackResult.content[0].json;
        }

        // Get variables for the top frame if we have a frameId
        let variablesData = null;
        let variablesError = null;
        if (breakpointInfo.frameId !== undefined && breakpointInfo.sessionId && breakpointInfo.threadId) {
            outputChannel.appendLine(`Attempting to get variables for frameId ${breakpointInfo.frameId}`);
            try {
                const variablesResult = await getStackFrameVariables({
                    sessionId: breakpointInfo.sessionId,
                    frameId: breakpointInfo.frameId,
                    threadId: breakpointInfo.threadId,
                });

                if (!variablesResult.isError && 'json' in variablesResult.content[0]) {
                    variablesData = variablesResult.content[0].json;
                    outputChannel.appendLine(`Successfully retrieved variables: ${JSON.stringify(variablesData)}`);
                } else {
                    // Capture the error message if there was one
                    variablesError = variablesResult.isError
                        ? 'text' in variablesResult.content[0]
                            ? variablesResult.content[0].text
                            : 'Unknown error'
                        : 'Invalid response format';
                    outputChannel.appendLine(`Failed to get variables: ${variablesError}`);
                }
            } catch (error) {
                variablesError = error instanceof Error ? error.message : String(error);
                outputChannel.appendLine(`Exception getting variables: ${variablesError}`);
            }
        } else {
            variablesError = 'Missing required information for variable inspection';
            outputChannel.appendLine(
                `Cannot get variables: ${variablesError} - frameId: ${breakpointInfo.frameId}, sessionId: ${breakpointInfo.sessionId}, threadId: ${breakpointInfo.threadId}`,
            );
        }

        // Construct a comprehensive response with all the debug information
        const debugInfo = {
            breakpoint: breakpointInfo,
            callStack: callStackData,
            variables: variablesData,
            variablesError: variablesError,
        };

        return {
            content: [
                {
                    type: 'text',
                    text: `Debug session ${
                        resolvedSessionName || breakpointInfo.sessionName
                    } ${actionType} successfully and stopped at ${
                        breakpointInfo.reason === 'breakpoint' ? 'a breakpoint' : `due to ${breakpointInfo.reason}`
                    }.`,
                },
                {
                    type: 'text',
                    text: JSON.stringify(debugInfo),
                },
            ],
            isError: false,
        };
    } catch (error) {
        return {
            content: [
                { type: 'text', text: `Debug session ${sessionName || sessionId} ${actionType} successfully.` },
                {
                    type: 'text',
                    text: `Warning: Failed to wait for debug session to stop: ${
                        error instanceof Error ? error.message : String(error)
                    }`,
                },
            ],
            isError: false,
        };
    }
}

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
 * @param params - Object containing workspaceFolder, configuration details, and optional waitForStop flag.
 */
export const startDebugSession = async (params: {
    workspaceFolder: string;
    configuration: { type: string; request: string; name: string; [key: string]: any };
    waitForStop?: boolean;
}) => {
    const { workspaceFolder, configuration, waitForStop = false } = params;
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

    // If waitForStop is true, wait for the debug session to stop at a breakpoint or other stopping point
    if (waitForStop) {
        return await waitForDebugSessionToStop({
            sessionName: configuration.name,
            actionType: 'started',
        });
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
    waitForStop: z
        .boolean()
        .optional()
        .default(false)
        .describe(
            'If true, the tool will wait until a breakpoint is hit or the debugger otherwise stops before returning. Prevents the LLM from getting impatient waiting for the breakpoint to hit.',
        ),
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
 * Resume execution of a debug session that has been paused (e.g., by a breakpoint).
 *
 * @param params - Object containing the sessionId of the debug session to resume and optional waitForStop flag.
 */
export const resumeDebugSession = async (params: { sessionId: string; waitForStop?: boolean }) => {
    const { sessionId, waitForStop = false } = params;

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
        outputChannel.appendLine(`Resuming debug session '${session.name}' (ID: ${sessionId})`);
        await session.customRequest('continue', { threadId: 0 }); // 0 means all threads

        // If waitForStop is true, wait for the debug session to stop at a breakpoint or other stopping point
        if (waitForStop) {
            return await waitForDebugSessionToStop({
                sessionId,
                sessionName: session.name,
                actionType: 'resumed',
            });
        }

        // If not waiting for stop, return immediately
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
    waitForStop: z
        .boolean()
        .optional()
        .default(false)
        .describe(
            'If true, the tool will wait until a breakpoint is hit or the debugger otherwise stops before returning. Provides detailed information about the stopped state.',
        ),
});
