// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { ContentExport } from '../App/ContentExport';

interface AssistantExportProps {
    assistantId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantExport: React.FC<AssistantExportProps> = (props) => {
    const { assistantId, iconOnly, asToolbarButton } = props;
    const workbenchService = useWorkbenchService();

    return (
        <ContentExport
            id={assistantId}
            contentTypeLabel="assistant"
            exportFunction={workbenchService.exportAssistantAsync}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
