// Copyright (c) Microsoft. All rights reserved.

import { generateUuid } from '@azure/ms-rest-js';
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
} from '@fluentui/react-components';
import React from 'react';
import { ConversationDefinition } from '../../../models/WorkflowDefinition';

interface ConversationDefinitionCreateProps {
    open: boolean;
    onOpenChange?: (open: boolean) => void;
    onCreate?: (conversationDefinition: ConversationDefinition) => void;
}

export const ConversationDefinitionCreate: React.FC<ConversationDefinitionCreateProps> = (props) => {
    const { open, onOpenChange, onCreate } = props;
    const [title, setTitle] = React.useState('');

    const handleSave = () => {
        onOpenChange?.(false);
        onCreate?.({
            id: generateUuid(),
            title,
        });
    };

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
                        <DialogContent>
                            <p>
                                <Field label="Title">
                                    <Input
                                        value={title}
                                        onChange={(_event, data) => setTitle(data?.value)}
                                        aria-autocomplete="none"
                                    />
                                </Field>
                            </p>
                            <button type="submit" hidden />
                        </DialogContent>
                        <DialogActions>
                            <DialogTrigger disableButtonEnhancement>
                                <Button appearance="secondary">Cancel</Button>
                            </DialogTrigger>
                            <DialogTrigger>
                                <Button appearance="primary" onClick={handleSave}>
                                    Save
                                </Button>
                            </DialogTrigger>
                        </DialogActions>
                    </DialogBody>
                </form>
            </DialogSurface>
        </Dialog>
    );
};
