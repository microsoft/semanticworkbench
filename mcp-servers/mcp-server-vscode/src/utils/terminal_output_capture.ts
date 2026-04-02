import * as vscode from 'vscode';

interface CommandRecord {
    command: string;
    output: string;
}

/** Terminal name → array of command records (most recent last) */
const commandHistory = new Map<string, CommandRecord[]>();

/** Maximum number of command records to keep per terminal */
const MAX_HISTORY_PER_TERMINAL = 50;

/**
 * Initialize terminal output capture using shell execution events.
 *
 * Listens to `onDidStartTerminalShellExecution` to capture per-command
 * output via `TerminalShellExecution.read()`. This is a stable API (1.93+)
 * that returns clean output without ANSI escape codes.
 *
 * Requires VS Code shell integration to be active (enabled by default).
 */
export const initTerminalOutputCapture = (context: vscode.ExtensionContext) => {
    const startListener = vscode.window.onDidStartTerminalShellExecution(async (event) => {
        const terminalName = event.terminal.name;
        const execution = event.execution;
        const chunks: string[] = [];

        for await (const data of execution.read()) {
            chunks.push(data);
        }

        const commandLine = execution.commandLine?.value ?? '(unknown)';
        const record: CommandRecord = {
            command: commandLine,
            output: chunks.join(''),
        };

        if (!commandHistory.has(terminalName)) {
            commandHistory.set(terminalName, []);
        }

        const history = commandHistory.get(terminalName)!;
        history.push(record);

        // Evict oldest records if over limit
        if (history.length > MAX_HISTORY_PER_TERMINAL) {
            history.splice(0, history.length - MAX_HISTORY_PER_TERMINAL);
        }
    });

    const closeListener = vscode.window.onDidCloseTerminal((terminal) => {
        commandHistory.delete(terminal.name);
    });

    context.subscriptions.push(startListener, closeListener, {
        dispose: () => {
            commandHistory.clear();
        },
    });
};

/** Get the command history for a terminal. */
export const getCommandHistory = (name: string): CommandRecord[] | undefined => commandHistory.get(name);
