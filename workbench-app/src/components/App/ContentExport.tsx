// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { CommandButton } from './CommandButton';

interface ContentExportProps {
    id: string;
    contentTypeLabel: string;
    exportFunction: (id: string) => Promise<{ blob: Blob; filename: string }>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ContentExport: React.FC<ContentExportProps> = (props) => {
    const { id, contentTypeLabel, exportFunction, iconOnly, asToolbarButton } = props;

    const exportContent = async () => {
        const { blob, filename } = await exportFunction(id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <CommandButton
            description={`Export ${contentTypeLabel}`}
            icon={<ArrowDownload24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Export"
            onClick={exportContent}
        />
    );
};
