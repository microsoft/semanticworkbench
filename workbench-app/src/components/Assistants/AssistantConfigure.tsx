// Copyright (c) Microsoft. All rights reserved.

import { DialogOpenChangeData, DialogOpenChangeEvent, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { DialogControl } from '../App/DialogControl';
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

interface AssistantConfigureDialogProps {
    assistant?: Assistant;
    open: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantConfigureDialog: React.FC<AssistantConfigureDialogProps> = (props) => {
    const { assistant, open, onOpenChange } = props;
    const classes = useClasses();
    const [isDirty, setIsDirty] = React.useState(false);

    const handleOpenChange = React.useCallback(
        (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            if (data.open) {
                setIsDirty(false);
                return;
            }

            if (isDirty) {
                const result = window.confirm('Are you sure you want to close without saving?');
                if (!result) {
                    return;
                }
            }

            setIsDirty(false);
            onOpenChange(event, data);
        },
        [isDirty, onOpenChange],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={handleOpenChange}
            title={assistant && `Configure "${assistant.name}"`}
            content={
                <div className={classes.content}>
                    {assistant && <AssistantConfiguration assistant={assistant} onIsDirtyChange={setIsDirty} />}
                </div>
            }
            classNames={{
                dialogSurface: classes.dialogSurface,
                dialogContent: classes.dialogContent,
            }}
        />
    );
};
