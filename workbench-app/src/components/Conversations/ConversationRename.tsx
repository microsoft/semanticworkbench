// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { useNotify } from '../../libs/useNotify';
import { Utility } from '../../libs/Utility';
import { useUpdateConversationMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

export const useConversationRenameControls = (id: string, value: string) => {
    const [updateConversation] = useUpdateConversationMutation();
    const [newTitle, setNewTitle] = React.useState(value);
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = React.useCallback(
        async (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => {
            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await updateConversation({ id, title: newTitle });
                    await onRename?.(id, newTitle);
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [id, newTitle, updateConversation],
    );

    const renameConversationForm = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>) => (
            <form
                onSubmit={(event) => {
                    event.preventDefault();
                    handleRename(onRename);
                }}
            >
                <Field label="Title">
                    <Input disabled={submitted} value={newTitle} onChange={(_event, data) => setNewTitle(data.value)} />
                </Field>
            </form>
        ),
        [handleRename, newTitle, submitted],
    );

    const renameConversationButton = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="rename"
                disabled={!newTitle || submitted}
                onClick={() => handleRename(onRename, onError)}
                appearance="primary"
            >
                {submitted ? 'Renaming...' : 'Rename'}
            </Button>
        ),
        [handleRename, newTitle, submitted],
    );

    return {
        renameConversationForm,
        renameConversationButton,
    };
};

interface ConversationRenameDialogProps {
    conversationId: string;
    value: string;
    onRename: (id: string, value: string) => Promise<void>;
    open?: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const ConversationRenameDialog: React.FC<ConversationRenameDialogProps> = (props) => {
    const { conversationId, value, onRename, open, onOpenChange } = props;
    const { renameConversationForm, renameConversationButton } = useConversationRenameControls(conversationId, value);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'error',
                title: 'Rename conversation failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Rename conversation"
            content={renameConversationForm(onRename)}
            closeLabel="Cancel"
            additionalActions={[renameConversationButton(onRename, handleError)]}
        />
    );
};

interface ConversationRenameProps {
    conversationId: string;
    disabled?: boolean;
    value: string;
    onRename?: (conversationId: string, value: string) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationRename: React.FC<ConversationRenameProps> = (props) => {
    const { conversationId, value, onRename, disabled, iconOnly, asToolbarButton } = props;
    const { renameConversationForm, renameConversationButton } = useConversationRenameControls(conversationId, value);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<EditRegular />}
            label="Rename"
            disabled={disabled}
            description="Rename conversation"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: 'Rename conversation',
                content: renameConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [renameConversationButton(onRename)],
            }}
        />
    );
};
