// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
import { PlugDisconnectedRegular } from '@fluentui/react-icons';
import React from 'react';
import { WorkflowDefinition } from '../../models/WorkflowDefinition';
import { useUpdateWorkflowDefinitionParticipantMutation } from '../../services/workbench/workflow';
import { CommandButton } from '../App/CommandButton';

interface WorkflowRemoveProps {
    workflowDefinition: WorkflowDefinition;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const WorkflowRemove: React.FC<WorkflowRemoveProps> = (props) => {
    const { workflowDefinition, onRemove, iconOnly, asToolbarButton } = props;
    const [updateWorkflowDefinitionParticipant] = useUpdateWorkflowDefinitionParticipantMutation();

    const handleRemove = React.useCallback(async () => {
        await updateWorkflowDefinitionParticipant({
            workflowDefinitionId: workflowDefinition.id,
            participantId: 'me',
            active: false,
        });
        onRemove?.();
    }, [workflowDefinition, onRemove, updateWorkflowDefinitionParticipant]);

    return (
        <CommandButton
            description="Remove workflow"
            icon={<PlugDisconnectedRegular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Remove"
            dialogContent={{
                title: 'Remove Workflow',
                content: (
                    <>
                        <Label> Are you sure you want to remove this workflow?</Label>
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
