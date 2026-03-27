import * as vscode from 'vscode';
import { z } from 'zod';
import { getCommandHistory } from '../utils/terminal_output_capture';

// Zod schema for create_terminal parameters
export const createTerminalSchema = z.object({
    name: z.string().optional().describe('Display name for the terminal tab.'),
    cwd: z.string().optional().describe('Working directory for the terminal.'),
    command: z.string().optional().describe('Command to execute immediately after terminal creation.'),
    show: z.boolean().default(true).describe('Whether to focus the terminal after creation.'),
});

/** Create a new terminal in the workspace. */
export const createTerminal = async (params: z.infer<typeof createTerminalSchema>) => {
    const { name, cwd, command, show } = params;

    const terminal = vscode.window.createTerminal({ name, cwd });

    if (show) {
        terminal.show();
    }

    if (command) {
        terminal.sendText(command);
    }

    const terminalName = terminal.name;

    return {
        content: [{ type: 'text', text: `Terminal '${terminalName}' created successfully.` }],
        isError: false,
    };
};

// Zod schema for list_terminals (no parameters)
export const listTerminalsSchema = z.object({});

/** List all active terminals in the workspace. */
export const listTerminals = () => {
    const terminals = vscode.window.terminals.map((terminal: vscode.Terminal, index: number) => ({
        index,
        name: terminal.name,
        processId: terminal.processId,
    }));

    return {
        content: [{ type: 'json', json: { terminals } }],
        isError: false,
    };
};

// Zod schema for send_terminal_text parameters
export const sendTerminalTextSchema = z.object({
    name: z.string().describe('Name of the target terminal.'),
    text: z.string().describe('Text to send to the terminal.'),
    addNewLine: z.boolean().default(true).describe('Whether to append a newline (simulating Enter key).'),
});

/** Send text to an existing terminal by name. */
export const sendTerminalText = async (params: z.infer<typeof sendTerminalTextSchema>) => {
    const { name, text, addNewLine } = params;
    const terminal = vscode.window.terminals.find((t: vscode.Terminal) => t.name === name);

    if (!terminal) {
        return {
            content: [{ type: 'text', text: `No terminal found with name '${name}'.` }],
            isError: true,
        };
    }

    terminal.sendText(text, addNewLine);
    terminal.show();

    return {
        content: [{ type: 'text', text: `Sent text to terminal '${name}'.` }],
        isError: false,
    };
};

// Zod schema for close_terminal parameters
export const closeTerminalSchema = z.object({
    name: z.string().describe('Name of the terminal to close.'),
});

// Zod schema for get_terminal_output parameters
export const getTerminalOutputSchema = z.object({
    name: z.string().describe('Name of the terminal to read output from.'),
    commandIndex: z
        .number()
        .int()
        .optional()
        .describe('Index of a specific command to read (0-based, most recent last). Omit to get all recent commands.'),
    limit: z
        .number()
        .int()
        .min(1)
        .max(50)
        .default(10)
        .describe('Maximum number of recent commands to return (when commandIndex is not specified).'),
});

/**
 * Read captured command output from a terminal.
 *
 * Output is captured per-command via shell execution events (stable API 1.93+).
 * Returns clean output without ANSI escape codes. Requires shell integration.
 */
export const getTerminalOutput = async (params: z.infer<typeof getTerminalOutputSchema>) => {
    const { name, commandIndex, limit } = params;
    const history = getCommandHistory(name);

    if (!history || history.length === 0) {
        return {
            content: [{ type: 'text', text: `No output captured for terminal '${name}'. Shell integration may not be active.` }],
            isError: true,
        };
    }

    if (commandIndex !== undefined) {
        if (commandIndex < 0 || commandIndex >= history.length) {
            return {
                content: [{ type: 'text', text: `Command index ${commandIndex} out of range (0-${history.length - 1}).` }],
                isError: true,
            };
        }
        const record = history[commandIndex];
        return {
            content: [{ type: 'text', text: JSON.stringify({ command: record.command, output: record.output, index: commandIndex }) }],
            isError: false,
        };
    }

    const recent = history.slice(-limit);
    return {
        content: [
            {
                type: 'text',
                text: JSON.stringify({
                    commands: recent.map((r, i) => ({ index: history.length - recent.length + i, command: r.command, output: r.output })),
                    totalCommands: history.length,
                }),
            },
        ],
        isError: false,
    };
};

/** Close a terminal by name. */
export const closeTerminal = async (params: z.infer<typeof closeTerminalSchema>) => {
    const { name } = params;
    const terminal = vscode.window.terminals.find((t: vscode.Terminal) => t.name === name);

    if (!terminal) {
        return {
            content: [{ type: 'text', text: `No terminal found with name '${name}'.` }],
            isError: true,
        };
    }

    terminal.dispose();

    return {
        content: [{ type: 'text', text: `Closed terminal '${name}'.` }],
        isError: false,
    };
};
