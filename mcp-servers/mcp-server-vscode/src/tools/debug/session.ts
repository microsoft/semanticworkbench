import * as vscode from 'vscode';
import { z } from 'zod';
import { activeSessions } from './common';

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
        try {
            // Import the waitForBreakpointHit function from events.ts
            const { waitForBreakpointHit } = await import('./events');

            // Wait for the debug session to stop
            const stopResult = await waitForBreakpointHit({
                sessionName: configuration.name,
                timeout: 30000, // Default timeout of 30 seconds
            });

            if (stopResult.isError) {
                return {
                    content: [
                        { type: 'text', text: `Debug session '${configuration.name}' started successfully.` },
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

            return {
                content: [
                    {
                        type: 'text',
                        text: `Debug session '${configuration.name}' started successfully and stopped at a breakpoint.`,
                    },
                    {
                        type: 'text',
                        text:
                            'json' in stopResult.content[0]
                                ? JSON.stringify(stopResult.content[0].json)
                                : 'Breakpoint hit, but no details available',
                    },
                ],
                isError: false,
            };
        } catch (error) {
            return {
                content: [
                    { type: 'text', text: `Debug session '${configuration.name}' started successfully.` },
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
