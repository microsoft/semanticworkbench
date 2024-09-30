// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
import { Delete24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { useDeleteAssistantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface AssistantDeleteProps {
    assistant: Assistant;
    onDelete?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantDelete: React.FC<AssistantDeleteProps> = (props) => {
    const { assistant, onDelete, iconOnly, asToolbarButton } = props;
    const [deleteAssistant] = useDeleteAssistantMutation();

    const handleDelete = React.useCallback(async () => {
        await deleteAssistant(assistant.id);
        onDelete?.();
    }, [assistant, onDelete, deleteAssistant]);

    return (
        <CommandButton
            description="Delete assistant"
            icon={<Delete24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Delete"
            dialogContent={{
                title: 'Delete Assistant',
                content: (
                    <p>
                        <Label> Are you sure you want to delete this assistant?</Label>
                    </p>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete">
                        <Button appearance="primary" onClick={handleDelete}>
                            Delete
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
