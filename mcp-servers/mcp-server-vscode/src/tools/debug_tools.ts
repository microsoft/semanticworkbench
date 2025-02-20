import * as vscode from 'vscode';
import { z } from 'zod';

/**
 * List all active debug sessions in the workspace.
 *
 * Exposes debug session information, including each session's ID, name, and associated launch configuration.
 */
export const listDebugSessions = () => {
    // Retrieve all active debug sessions
    const sessions = vscode.debug.sessions.map((session: vscode.DebugSession) => ({
        id: session.id,
        name: session.name,
        configuration: session.configuration
    }));

    // Return session list
    return {
        content: [
            {
                type: 'json',
                json: { sessions }
            }
        ],
        isError: false
    };
};

// Zod schema for validating tool parameters (none for this tool)
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
    // Ensure that workspace folders exist and are accessible
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
        isError: false
    };
};

// Zod schema for validating start_debug_session parameters
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
