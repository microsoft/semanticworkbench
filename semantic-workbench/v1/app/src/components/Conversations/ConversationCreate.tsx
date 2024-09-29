// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Dialog,
    DialogActions,
    DialogBody,
    DialogContent,
    DialogOpenChangeData,
    DialogOpenChangeEvent,
    DialogSurface,
    DialogTitle,
    DialogTrigger,
    Field,
    Input,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useCreateConversationMutation } from '../../services/workbench';

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
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogSurface>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        handleSave();
                    }}
                >
                    <DialogBody>
                        <DialogTitle>New Conversation</DialogTitle>
                        <DialogContent className={classes.dialogContent}>
                            <Field label="Title">
                                <Input
                                    disabled={submitted}
                                    value={title}
                                    onChange={(_event, data) => setTitle(data?.value)}
                                    aria-autocomplete="none"
                                />
                            </Field>
                            <button disabled={submitted} type="submit" hidden />
                        </DialogContent>
                        <DialogActions>
                            <DialogTrigger disableButtonEnhancement>
                                <Button appearance="secondary">Cancel</Button>
                            </DialogTrigger>
                            <DialogTrigger>
                                <Button disabled={!title || submitted} appearance="primary" onClick={handleSave}>
                                    {submitted ? 'Saving...' : 'Save'}
                                </Button>
                            </DialogTrigger>
                        </DialogActions>
                    </DialogBody>
                </form>
            </DialogSurface>
        </Dialog>
    );
};
