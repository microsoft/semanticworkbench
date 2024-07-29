// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { Copy24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Assistant } from '../../models/Assistant';
import { CommandButton } from '../App/CommandButton';

interface AssistantDuplicateProps {
    assistant: Assistant;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    onDuplicate?: (assistant: Assistant) => void;
    onDuplicateError?: (error: Error) => void;
}

export const AssistantDuplicate: React.FC<AssistantDuplicateProps> = (props) => {
    const { assistant, iconOnly, asToolbarButton, onDuplicate, onDuplicateError } = props;
    const workbenchService = useWorkbenchService();

    const duplicateAssistant = async () => {
        try {
            const duplicate = await workbenchService.duplicateAssistantAsync(assistant.id);
            onDuplicate?.(duplicate);
        } catch (error) {
            onDuplicateError?.(error as Error);
        }
    };

    return (
        <CommandButton
            description="Duplicate assistant"
            icon={<Copy24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Duplicate"
            dialogContent={{
                title: 'Duplicate assistant',
                content: 'Are you sure you want to duplicate this assistant?',
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="duplicate">
                        <Button appearance="primary" onClick={duplicateAssistant}>
                            Duplicate
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
