// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useExportUtility } from '../../libs/useExportUtility';
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
    const { exportContent } = useExportUtility();
    const [exporting, setExporting] = React.useState(false);

    const handleExport = React.useCallback(async () => {
        if (exporting) {
            return;
        }
        setExporting(true);

        try {
            await exportContent(id, exportFunction);
        } finally {
            setExporting(false);
        }
    }, [exporting, exportContent, id, exportFunction]);

    return (
        <CommandButton
            description={`Export ${contentTypeLabel}`}
            icon={<ArrowDownload24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label={exporting ? 'Exporting...' : 'Export'}
            onClick={handleExport}
            disabled={exporting}
        />
    );
};
