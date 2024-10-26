// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import { SettingsRegular } from '@fluentui/react-icons';
import React from 'react';
import { useGetAssistantQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { AssistantEdit } from './AssistantEdit';
import { AssistantServiceMetadata } from './AssistantServiceMetadata';

const useClasses = makeStyles({
    dialogSurface: {
        maxWidth: 'calc(min(1000px, 100vw) - 32px)',
        minWidth: 'min(600px, 100vw)',
        width: 'fit-content',
    },
    dialogContent: {
        height: 'calc(100vh - 150px)',
        width: 'calc(min(1000px, 100vw) - 100px)',
        paddingRight: '8px',
        boxSizing: 'border-box',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface AssistantConfigureProps {
    assistantId: string;
    disabled?: boolean;
}

export const AssistantConfigure: React.FC<AssistantConfigureProps> = (props) => {
    const { assistantId, disabled } = props;
    const classes = useClasses();
    const { data: assistant, error: assistantError, isLoading: assistantLoading } = useGetAssistantQuery(assistantId);

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant (${assistantId}): ${errorMessage}`);
    }

    if (assistantLoading) {
        return null;
    }

    if (!assistant) {
        throw new Error(`Assistant (${assistantId}) not found`);
    }

    return (
        <CommandButton
            icon={<SettingsRegular />}
            iconOnly
            disabled={disabled}
            description={disabled ? `Workflow assistants cannot be configured` : 'Edit assistant configuration'}
            dialogContent={{
                title: `Configure "${assistant.name}"`,
                content: (
                    <div className={classes.content}>
                        <AssistantServiceMetadata assistantServiceId={assistant.assistantServiceId} />
                        <AssistantEdit assistant={assistant} />
                    </div>
                ),
                closeLabel: 'Close',
                classNames: {
                    dialogSurface: classes.dialogSurface,
                    dialogContent: classes.dialogContent,
                },
            }}
        />
    );
};
