// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogTrigger,
    Field,
    Input,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useCreateConversationMutation } from '../../services/workbench';
import { DialogControl } from '../App/DialogControl';

const useClasses = makeStyles({
    dialogContent: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalM,
    },
});

interface ConversationCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (conversation: Conversation) => void;
    metadata?: {
        [key: string]: any;
    };
}

export const ConversationCreate: React.FC<ConversationCreateProps> = (props) => {
    const { open, onOpenChange, onCreate, metadata } = props;
    const classes = useClasses();
    const [createConversation] = useCreateConversationMutation();
    const [title, setTitle] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);

    const handleSave = async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const conversation = await createConversation({ title, metadata }).unwrap();
            onOpenChange?.(false);
            onCreate?.(conversation);
        } finally {
            setSubmitted(false);
        }
    };

    React.useEffect(() => {
        if (!open) {
            return;
        }
        setTitle('');
        setSubmitted(false);
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
            classNames={{
                dialogContent: classes.dialogContent,
            }}
            onOpenChange={handleOpenChange}
            title="New Conversation"
            content={
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <Field label="Title">
                        <Input disabled={submitted} value={title} onChange={(_event, data) => setTitle(data.value)} />
                    </Field>
                    <button disabled={!title || submitted} type="submit" hidden />
                </form>
            }
            closeLabel="Cancel"
            additionalActions={[
                <DialogTrigger key="save" disableButtonEnhancement>
                    <Button disabled={!title || submitted} appearance="primary" onClick={handleSave}>
                        {submitted ? 'Saving...' : 'Save'}
                    </Button>
                </DialogTrigger>,
            ]}
        />
    );
};
