// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../../libs/useWorkbenchService';
import { WorkflowDefinition } from '../../../models/WorkflowDefinition';
import { CommandButton } from '../../App/CommandButton';

interface WorkflowExportProps {
    workflowDefinition: WorkflowDefinition;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const WorkflowExport: React.FC<WorkflowExportProps> = (props) => {
    const { workflowDefinition, iconOnly, asToolbarButton } = props;
    const workbenchService = useWorkbenchService();

    const exportWorkflow = async () => {
        const { blob, filename } = await workbenchService.exportWorkflowDefinitionAsync(workflowDefinition.id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <CommandButton
            description="Export workflow"
            icon={<ArrowDownload24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Export"
            onClick={exportWorkflow}
        />
    );
};
