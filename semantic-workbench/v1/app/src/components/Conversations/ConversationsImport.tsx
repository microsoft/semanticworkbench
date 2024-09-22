// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { ContentImport } from '../App/ContentImport';

interface ConversationsImportProps {
    disabled?: boolean;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onImport?: (conversationIds: string[]) => void;
    onError?: (error: Error) => void;
}

export const ConversationsImport: React.FC<ConversationsImportProps> = (props) => {
    const { disabled, iconOnly, asToolbarButton, onImport, onError } = props;
    const workbenchService = useWorkbenchService();

    const importFile = async (file: File) => {
        const result = await workbenchService.importConversationsAsync(file);
        return result.conversationIds;
    };

    return (
        <ContentImport
            contentTypeLabel="conversations"
            importFunction={importFile}
            onImport={onImport}
            onError={onError}
            disabled={disabled}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
