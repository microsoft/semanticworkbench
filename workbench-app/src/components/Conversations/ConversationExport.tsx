// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
import { ContentExport } from '../App/ContentExport';

interface ConversationExportProps {
    conversationId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationExport: React.FC<ConversationExportProps> = (props) => {
    const { conversationId, iconOnly, asToolbarButton } = props;
    const { exportConversationFunction } = useExportUtility();

    return (
        <ContentExport
            id={conversationId}
            contentTypeLabel="conversation"
            exportFunction={exportConversationFunction}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
