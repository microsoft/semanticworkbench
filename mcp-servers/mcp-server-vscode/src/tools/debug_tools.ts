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
