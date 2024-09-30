// Copyright (c) Microsoft. All rights reserved.

import { Card, Label, Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { AssistantServiceRegistration } from '../../models/AssistantServiceRegistration';
import { useGetAssistantServiceRegistrationsQuery } from '../../services/workbench';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
        gap: tokens.spacingVerticalM,
        borderRadius: tokens.borderRadiusMedium,
        ...shorthands.padding(tokens.spacingVerticalM),
    },
    data: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
    },
});

interface AssistantServiceMetadataProps {
    assistantServiceId: string;
}

export const AssistantServiceMetadata: React.FC<AssistantServiceMetadataProps> = (props) => {
    const { assistantServiceId } = props;
    const classes = useClasses();

    const {
        data: assistantServices,
        isLoading: isAssistantServicesLoading,
        isError: getAssistantServicesError,
    } = useGetAssistantServiceRegistrationsQuery({});

    if (getAssistantServicesError) {
        const errorMessage = JSON.stringify(getAssistantServicesError);
        throw new Error(`Error loading assistant services: ${errorMessage}`);
    }

    const [assistantService, setAssistantService] = React.useState<AssistantServiceRegistration | undefined>(undefined);

    React.useEffect(() => {
        const service = assistantServices?.find((service) => service.assistantServiceId === assistantServiceId);

        if (service) {
            setAssistantService(service);
        }
    }, [assistantServiceId, assistantServices, setAssistantService]);

    if (isAssistantServicesLoading) return null;
    if (!assistantService) return null;

    return (
        <Card className={classes.root}>
            <Text size={400} weight="semibold">
                Assistant Backend
            </Text>
            <div className={classes.data}>
                <Label weight="semibold">{assistantService.name}</Label>
                <Label>
                    <em>{assistantService.description}</em>
                </Label>
                <Label size="small">Assistant service ID: {assistantService.assistantServiceId}</Label>
                <Label size="small">Hosted at: {assistantService.assistantServiceUrl}</Label>
                <Label size="small">
                    Created by: {assistantService.createdByUserName} [{assistantService.createdByUserId}]
                </Label>
            </div>
        </Card>
    );
};
