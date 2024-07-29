// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
import { PlugDisconnectedRegular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowRun } from '../../models/WorkflowRun';
import { useDeleteWorkflowRunMutation } from '../../services/workbench/workflow';
import { CommandButton } from '../App/CommandButton';

interface WorkflowRunRemoveProps {
    workflowRun: WorkflowRun;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const WorkflowRunRemove: React.FC<WorkflowRunRemoveProps> = (props) => {
    const { workflowRun, onRemove, iconOnly, asToolbarButton } = props;
    const [deleteWorkflowRun] = useDeleteWorkflowRunMutation();

    const handleRemove = React.useCallback(async () => {
        await deleteWorkflowRun(workflowRun.id);
        onRemove?.();
    }, [workflowRun, onRemove, deleteWorkflowRun]);

    return (
        <CommandButton
            description="Remove workflow run"
            icon={<PlugDisconnectedRegular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Remove"
            dialogContent={{
                title: 'Remove Workflow Run',
                content: (
                    <>
                        <Label> Are you sure you want to remove this workflow run?</Label>
                    </>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="remove">
                        <Button appearance="primary" onClick={handleRemove}>
                            Remove
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
