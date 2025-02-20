import getPort from 'get-port';
import * as vscode from 'vscode';

export async function resolvePort(desiredPort: number): Promise<number> {
    // Try to get the desired port or the next available port
    const availablePort = await getPort({ port: desiredPort });

    // If the available port is not the same as the desired port, prompt the user
    if (availablePort !== desiredPort) {
        const userInput = await vscode.window.showInputBox({
            prompt: `Port ${desiredPort} is in use. Enter a new port or press Enter to use the available port (${availablePort}):`,
            value: String(availablePort),
            validateInput: (input) => {
                const num = Number(input);
                if (isNaN(num) || num < 1 || num > 65535) {
                    return 'Please enter a valid port number (1-65535).';
                }
                return null;
            },
        });
        if (userInput && userInput.trim().length > 0) {
            const newPort = Number(userInput);
            return resolvePort(newPort);
        }
        return availablePort;
    }
    return availablePort;
}
