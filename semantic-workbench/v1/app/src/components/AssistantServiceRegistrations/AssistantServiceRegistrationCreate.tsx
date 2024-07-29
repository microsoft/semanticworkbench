// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Checkbox,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    Field,
    Input,
    Textarea,
} from '@fluentui/react-components';
import React from 'react';
import { Form } from 'react-router-dom';
import {
    AssistantServiceRegistration,
    NewAssistantServiceRegistration,
} from '../../models/AssistantServiceRegistration';
import {
    useCreateAssistantServiceRegistrationMutation,
    useGetAssistantServiceRegistrationsQuery,
} from '../../services/workbench';
import { AssistantServiceRegistrationApiKey } from './AssistantServiceRegistrationApiKey';

interface AssistantServiceRegistrationCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (assistantServiceRegistration: AssistantServiceRegistration) => void;
}

export const AssistantServiceRegistrationCreate: React.FC<AssistantServiceRegistrationCreateProps> = (props) => {
    const { open, onOpenChange, onCreate } = props;
    const { refetch: refetchAssistantServiceRegistrations } = useGetAssistantServiceRegistrationsQuery({});
    const [createAssistantServiceRegistration] = useCreateAssistantServiceRegistrationMutation();
    const [name, setName] = React.useState('');
    const [includeInListing, setIncludeInListing] = React.useState(false);
    const [description, setDescription] = React.useState('');
    const [id, setId] = React.useState('');
    const [valid, setValid] = React.useState(false);
    const [submitted, setSubmitted] = React.useState(false);
    const [apiKey, setApiKey] = React.useState<string>();

    const handleSave = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        const newAssistantServiceRegistration: NewAssistantServiceRegistration = {
            assistantServiceId: id,
            name,
            description,
            includeInListing,
        };

        try {
            const assistantServiceRegistration = await createAssistantServiceRegistration(
                newAssistantServiceRegistration,
            ).unwrap();
            await refetchAssistantServiceRegistrations();
            onOpenChange?.(false);
            onCreate?.(assistantServiceRegistration);
            setApiKey(assistantServiceRegistration.apiKey);
        } finally {
            setSubmitted(false);
        }
    };

    const resetState = React.useCallback(() => {
        setValid(false);
        setId('');
        setName('');
        setIncludeInListing(false);
        setDescription('');
        setApiKey(undefined);
        setSubmitted(false);
    }, []);

    React.useEffect(() => {
        if (!open) {
            return;
        }
        resetState();
    }, [open, resetState]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (!data.open) {
                resetState();
            }
            onOpenChange?.(data.open);
        },
        [onOpenChange, resetState],
    );

    return (
        <>
            {apiKey && <AssistantServiceRegistrationApiKey apiKey={apiKey} onClose={() => setApiKey(undefined)} />}
            <Dialog open={open} onOpenChange={handleOpenChange}>
                <DialogSurface>
                    <DialogBody>
                        <DialogTitle>Create Assistant Service Registration</DialogTitle>
                        <DialogContent>
                            <Form>
                                <Field label="Assistant Service ID" required>
                                    <Input
                                        value={id}
                                        onChange={(event, data) => {
                                            // lowercase first
                                            data.value = data.value.toLowerCase();
                                            // limit to lowercase alphanumeric and hyphen
                                            data.value = data.value.replace(/[^a-z0-9-.]/g, '');

                                            setId(data.value);
                                            setValid(event.currentTarget.form!.checkValidity());
                                        }}
                                        aria-autocomplete="none"
                                        placeholder="Unique identifier for your assistant; eg: helpful-assistant.team-name"
                                    />
                                </Field>
                                <Field label="Name" required>
                                    <Input
                                        value={name}
                                        onChange={(event, data) => {
                                            setName(data.value);
                                            setValid(event.currentTarget.form!.checkValidity());
                                        }}
                                        aria-autocomplete="none"
                                        placeholder="Display name for your assistant; eg: Helpful Assistant"
                                    />
                                </Field>
                                <Checkbox
                                    label="Include this assistant service in everyone's create assistant list"
                                    checked={includeInListing}
                                    onChange={(_, data) => setIncludeInListing(data.checked === true)}
                                />
                                <Field label="Description">
                                    <Textarea
                                        value={description}
                                        onChange={(event, data) => {
                                            setDescription(data.value);
                                            setValid(event.currentTarget.form!.checkValidity());
                                        }}
                                        aria-autocomplete="none"
                                        placeholder="Description of your assistant; eg: A helpful assistant that can answer questions and provide guidance."
                                    />
                                </Field>
                            </Form>
                        </DialogContent>
                        <DialogActions>
                            <Button appearance="primary" onClick={handleSave} disabled={!valid || submitted}>
                                Save
                            </Button>
                            <Button onClick={() => onOpenChange?.(false)}>Cancel</Button>
                        </DialogActions>
                    </DialogBody>
                </DialogSurface>
            </Dialog>
        </>
    );
};
