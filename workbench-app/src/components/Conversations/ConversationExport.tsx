// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { ContentExport } from '../App/ContentExport';

interface ConversationExportProps {
    conversationId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationExport: React.FC<ConversationExportProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton } = props;
    const workbenchService = useWorkbenchService();

    const exportConversation = async (conversationId: string) => {
        return await workbenchService.exportConversationsAsync([conversationId]);
    };

    return (
        <ContentExport
            id={conversationId}
            contentTypeLabel="conversation"
            exportFunction={exportConversation}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
