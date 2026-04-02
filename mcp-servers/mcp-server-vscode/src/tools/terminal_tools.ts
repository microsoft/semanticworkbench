import * as vscode from 'vscode';
import { z } from 'zod';

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
