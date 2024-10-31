// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
import { KeyResetRegular } from '@fluentui/react-icons';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useResetAssistantServiceRegistrationApiKeyMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { AssistantServiceRegistrationApiKey } from './AssistantServiceRegistrationApiKey';

interface AssistantServiceRegistrationApiKeyResetProps {
    assistantServiceRegistration: AssistantServiceRegistration;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantServiceRegistrationApiKeyReset: React.FC<AssistantServiceRegistrationApiKeyResetProps> = (
    props,
) => {
    const { assistantServiceRegistration, onRemove, iconOnly, asToolbarButton } = props;
    const [resetAssistantServiceRegistrationApiKey] = useResetAssistantServiceRegistrationApiKeyMutation();
    const [submitted, setSubmitted] = React.useState(false);
    const [unmaskedApiKey, setUnmaskedApiKey] = React.useState<string | undefined>(undefined);

    const handleReset = React.useCallback(async () => {
        setSubmitted(true);
        let updatedRegistration: AssistantServiceRegistration | undefined;
        try {
            updatedRegistration = await resetAssistantServiceRegistrationApiKey(
                assistantServiceRegistration.assistantServiceId,
            ).unwrap();
        } finally {
            setSubmitted(false);
        }

        if (updatedRegistration) {
            setUnmaskedApiKey(updatedRegistration.apiKey);
        }

        onRemove?.();
    }, [assistantServiceRegistration.assistantServiceId, resetAssistantServiceRegistrationApiKey, onRemove]);

    return (
        <>
            {unmaskedApiKey && (
                <AssistantServiceRegistrationApiKey
                    apiKey={unmaskedApiKey}
                    onClose={() => setUnmaskedApiKey(undefined)}
                />
            )}
            <CommandButton
                disabled={submitted}
                description="Reset API Key"
                icon={<KeyResetRegular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label="Reset"
                dialogContent={{
                    title: 'Reset API Key',
                    content: (
                        <>
                            <p>
                                <Label>
                                    Are you sure you want to reset the API key for this assistant service registration?
                                </Label>
                            </p>
                            <p>
                                Any existing assistant services using the current API key will stop working. You will
                                need to update the API key in any assistant services that use it.
                            </p>
                        </>
                    ),
                    closeLabel: 'Cancel',
                    additionalActions: [
                        <DialogTrigger key="reset" disableButtonEnhancement>
                            <Button appearance="primary" onClick={handleReset}>
                                Reset
                            </Button>
                        </DialogTrigger>,
                    ],
                }}
            />
        </>
    );
};
