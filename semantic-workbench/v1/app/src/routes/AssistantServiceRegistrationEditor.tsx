// Copyright (c) Microsoft. All rights reserved.

import { Button, Card, Checkbox, Field, Input, Textarea, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParams } from 'react-router-dom';
import { AppView } from '../components/App/AppView';
import { Loading } from '../components/App/Loading';
import { AssistantServiceRegistrationApiKeyReset } from '../components/AssistantServiceRegistrations/AssistantServiceRegistrationApiKeyReset';
import {
    useGetAssistantServiceRegistrationQuery,
    useUpdateAssistantServiceRegistrationMutation,
} from '../services/workbench';

const useClasses = makeStyles({
    card: {
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    input: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'stretch',
        width: '100%',
        maxWidth: '300px',
    },
    row: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: tokens.spacingHorizontalM,
    },
});

export const AssistantServiceRegistrationEditor: React.FC = () => {
    const { assistantServiceRegistrationId } = useParams();
    if (!assistantServiceRegistrationId) {
        throw new Error('Assistant service registration ID is required');
    }
    const classes = useClasses();

    const {
        data: assistantServiceRegistration,
        error: assistantServiceRegistrationError,
        isLoading: isAssistantServiceRegistrationLoading,
    } = useGetAssistantServiceRegistrationQuery(assistantServiceRegistrationId);
    const [updateAssistantServiceRegistration] = useUpdateAssistantServiceRegistrationMutation();

    const [name, setName] = React.useState('');
    const [includeInListing, setIncludeInListing] = React.useState(false);
    const [description, setDescription] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);

    if (assistantServiceRegistrationError) {
        const errorMessage = JSON.stringify(assistantServiceRegistrationError);
        throw new Error(`Error loading assistant service registration: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (assistantServiceRegistration) {
            setName(assistantServiceRegistration.name);
            setIncludeInListing(assistantServiceRegistration.includeInListing);
            setDescription(assistantServiceRegistration.description);
        }
    }, [assistantServiceRegistration]);

    const handleSave = React.useCallback(async () => {
        setSubmitted(true);
        try {
            await updateAssistantServiceRegistration({
                id: assistantServiceRegistrationId,
                assistantServiceRegistration: {
                    name,
                    description,
                    includeInListing,
                },
            }).unwrap();
        } finally {
            setSubmitted(false);
        }
    }, [assistantServiceRegistrationId, name, includeInListing, description, updateAssistantServiceRegistration]);

    if (isAssistantServiceRegistrationLoading || !assistantServiceRegistration) {
        return (
            <AppView title="Assistant Service Registration Editor">
                <Loading />
            </AppView>
        );
    }

    const disabled =
        submitted ||
        !name ||
        !description ||
        (name === assistantServiceRegistration.name &&
            description === assistantServiceRegistration.description &&
            includeInListing === assistantServiceRegistration.includeInListing);

    return (
        <AppView title="Assistant Service Registration Editor">
            <Card className={classes.card}>
                <Field label="Assistant Service ID (read-only)">
                    <Input className={classes.input} value={assistantServiceRegistration.assistantServiceId} readOnly />
                </Field>
                <Field label="Name">
                    <Input className={classes.input} value={name} onChange={(_event, data) => setName(data.value)} />
                </Field>
                <Field label="API Key (read-only)">
                    <div className={classes.row}>
                        <Input className={classes.input} value={assistantServiceRegistration.apiKey} readOnly />
                        <AssistantServiceRegistrationApiKeyReset
                            assistantServiceRegistration={assistantServiceRegistration}
                        />
                    </div>
                </Field>
                <Checkbox
                    label="Include this assistant service in everyone's create assistant list"
                    checked={includeInListing}
                    onChange={(_event, data) => setIncludeInListing(data.checked === true)}
                />
                <Field label="Description">
                    <Textarea rows={4} value={description} onChange={(_event, data) => setDescription(data.value)} />
                </Field>
                <div>
                    <Button appearance="primary" disabled={disabled} onClick={handleSave}>
                        Save
                    </Button>
                </div>
            </Card>
        </AppView>
    );
};
