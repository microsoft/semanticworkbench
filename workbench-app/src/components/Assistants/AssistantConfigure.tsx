// Copyright (c) Microsoft. All rights reserved.

import { Button, makeStyles, tokens } from '@fluentui/react-components';
import { SettingsRegular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { CommandButton } from '../App/CommandButton';
import { AssistantConfiguration } from './AssistantConfiguration';

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
        overflowY: 'auto',
    },
    content: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface AssistantConfigureProps {
    assistant: Assistant;
    iconOnly?: boolean;
    disabled?: boolean;
    simulateMenuItem?: boolean;
}

export const AssistantConfigure: React.FC<AssistantConfigureProps> = (props) => {
    const { assistant, iconOnly, disabled, simulateMenuItem } = props;
    const classes = useClasses();
    const [open, setOpen] = React.useState(false);
    const [isDirty, setIsDirty] = React.useState(false);

    const handleClose = React.useCallback(() => {
        if (isDirty) {
            const result = window.confirm('Are you sure you want to close without saving?');
            if (!result) {
                return;
            }
        }
        setOpen(false);
    }, [isDirty]);

    return (
        <CommandButton
            open={open}
            onClick={() => setOpen(true)}
            icon={<SettingsRegular />}
            simulateMenuItem={simulateMenuItem}
            label="Configure"
            iconOnly={iconOnly}
            disabled={disabled}
            dialogContent={{
                title: `Configure "${assistant.name}"`,
                content: (
                    <div className={classes.content}>
                        <AssistantConfiguration assistant={assistant} onIsDirtyChange={setIsDirty} />
                    </div>
                ),
                hideDismissButton: true,
                classNames: {
                    dialogSurface: classes.dialogSurface,
                    dialogContent: classes.dialogContent,
                },
                additionalActions: [
                    <Button key="close" appearance="primary" onClick={handleClose}>
                        Close
                    </Button>,
                ],
            }}
        />
    );
};
