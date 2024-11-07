// Copyright (c) Microsoft. All rights reserved.

import { DialogTrigger } from '@fluentui/react-components';
import { DeleteRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useRemoveAssistantServiceRegistrationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface AssistantServiceRegistrationRemoveProps {
    assistantServiceRegistration: AssistantServiceRegistration;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantServiceRegistrationRemove: React.FC<AssistantServiceRegistrationRemoveProps> = (props) => {
    const { assistantServiceRegistration, onRemove, iconOnly, asToolbarButton } = props;
    const [removeAssistantServiceRegistration] = useRemoveAssistantServiceRegistrationMutation();
    const [submitted, setSubmitted] = React.useState(false);

    if (!assistantServiceRegistration) {
        throw new Error(`Assistant service registration not found`);
    }

    const handleAssistantServiceRegistrationRemove = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            await removeAssistantServiceRegistration(assistantServiceRegistration.assistantServiceId);
            onRemove?.();
        } finally {
            setSubmitted(false);
        }
    }, [assistantServiceRegistration.assistantServiceId, onRemove, removeAssistantServiceRegistration, submitted]);

    return (
        <CommandButton
            icon={<DeleteRegular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            description="Delete assistant service registration"
            dialogContent={{
                title: 'Delete Assistant Service Registration',
                content: (
                    <p>
                        Are you sure you want to delete the assistant service registration{' '}
                        <strong>{assistantServiceRegistration.name}</strong>?
                    </p>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete" disableButtonEnhancement>
                        <CommandButton
                            icon={<DeleteRegular />}
                            label="Delete"
                            onClick={handleAssistantServiceRegistrationRemove}
                        />
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
