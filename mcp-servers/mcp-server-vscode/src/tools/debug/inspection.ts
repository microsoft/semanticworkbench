import { z } from 'zod';
import { activeSessions, getCallStack } from './common';

// Re-export getCallStack and its schema
export { getCallStack };

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
