import React from 'react';
import { useWorkbenchService } from './useWorkbenchService';

export const useExportUtility = () => {
    const workbenchService = useWorkbenchService();

    const exportContent = React.useCallback(
        async (id: string, exportFunction: (id: string) => Promise<{ blob: Blob; filename: string }>) => {
            const { blob, filename } = await exportFunction(id);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        },
        [],
    );

    const exportConversationFunction = React.useCallback(
        async (conversationId: string) => {
            return await workbenchService.exportConversationsAsync([conversationId]);
        },
        [workbenchService],
    );

    const exportConversation = React.useCallback(
        async (conversationId: string) => {
            return await exportContent(conversationId, exportConversationFunction);
        },
        [exportContent, exportConversationFunction],
    );

    const exportAssistantFunction = React.useCallback(
        async (assistantId: string) => {
            return await workbenchService.exportAssistantAsync(assistantId);
        },
        [workbenchService],
    );

    const exportAssistant = React.useCallback(
        async (assistantId: string) => {
            return await exportContent(assistantId, exportAssistantFunction);
        },
        [exportContent, exportAssistantFunction],
    );

    return {
        exportContent,
        exportConversationFunction,
        exportConversation,
        exportAssistantFunction,
        exportAssistant,
    };
};
