// Copyright (c) Microsoft. All rights reserved.

import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
import { ContentExport } from '../App/ContentExport';

interface AssistantExportProps {
    assistantId: string;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantExport: React.FC<AssistantExportProps> = (props) => {
    const { assistantId, iconOnly, asToolbarButton } = props;
    const { exportAssistantFunction } = useExportUtility();

    return (
        <ContentExport
            id={assistantId}
            contentTypeLabel="assistant"
            exportFunction={exportAssistantFunction}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
        />
    );
};
