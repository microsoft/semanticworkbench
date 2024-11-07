// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    Field,
    Input,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { ConversationDefinition } from '../../../models/WorkflowDefinition';
import { DialogControl } from '../../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface ConversationDefinitionCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (conversationDefinition: ConversationDefinition) => void;
}

export const ConversationDefinitionCreate: React.FC<ConversationDefinitionCreateProps> = (props) => {
    const { open, onOpenChange, onCreate } = props;
    const classes = useClasses();
    const [title, setTitle] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);

    const handleSave = React.useCallback(() => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            onOpenChange?.(false);
            onCreate?.({
                id: generateUuid(),
                title,
            });
        } finally {
            setSubmitted(false);
        }
    }, [onCreate, onOpenChange, submitted, title]);

    React.useEffect(() => {
        if (!open) {
            return;
        }
        setTitle('');
    }, [open]);

    const handleOpenChange = React.useCallback(
        (_event: DialogOpenChangeEvent, data: DialogOpenChangeData) => {
            onOpenChange?.(data.open);
        },
        [onOpenChange],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={handleOpenChange}
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            title="New Conversation"
            content={
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <Field label="Title">
                        <Input
                            value={title}
                            onChange={(_event, data) => setTitle(data?.value)}
                            aria-autocomplete="none"
                        />
                    </Field>
                    <button type="submit" hidden />
                </form>
            }
            closeLabel="Cancel"
            additionalActions={[
                <Button key="save" appearance="primary" onClick={handleSave} disabled={submitted}>
                    {submitted ? 'Saving...' : 'Save'}
                </Button>,
            ]}
        />
    );
};
