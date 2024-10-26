// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { ContentExport, exportContent } from '../App/ContentExport';

export const useConversationExport = () => {
    const workbenchService = useWorkbenchService();

    const exportFunction = async (conversationId: string) => {
        return await workbenchService.exportConversationsAsync([conversationId]);
    };

    const exportConversation = async (conversationId: string) => {
        return await exportContent(conversationId, exportFunction);
    };

    return {
        exportFunction,
        exportConversation,
    };
};

interface ConversationExportProps {
    conversationId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationExport: React.FC<ConversationExportProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton } = props;
    const { exportFunction } = useConversationExport();

    return (
        <ContentExport
            id={conversationId}
            contentTypeLabel="conversation"
            exportFunction={exportFunction}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
