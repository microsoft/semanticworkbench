// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent, Field, Input } from '@fluentui/react-components';
import { EditRegular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { useNotify } from '../../libs/useNotify';
import { Assistant } from '../../models/Assistant';
import { useGetConversationParticipantsQuery, useUpdateAssistantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useAssistantRenameControls = (assistant?: Assistant, conversationId?: string) => {
    const [updateAssistant] = useUpdateAssistantMutation();
    const { refetch: refetchParticipants } = useGetConversationParticipantsQuery(conversationId ?? '', {
        skip: !conversationId,
    });
    const [newName, setNewName] = React.useState<string>();
    const [submitted, setSubmitted] = React.useState(false);

    const handleRename = React.useCallback(
        async (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => {
            if (!assistant || !newName || submitted) {
                return;
            }

            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await updateAssistant({ ...assistant, name: newName });
                    await onRename?.(assistant.id, newName);

                    // Refetch participants to update the assistant name in the list
                    if (conversationId) {
                        await refetchParticipants();
                    }
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [assistant, conversationId, newName, refetchParticipants, submitted, updateAssistant],
    );

    const renameAssistantForm = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>) => (
            <form
                onSubmit={(event) => {
                    event.preventDefault();
                    handleRename(onRename);
                }}
            >
                <Field label="Name">
                    <Input
                        disabled={submitted}
                        defaultValue={assistant?.name}
                        onChange={(_event, data) => setNewName(data.value)}
                    />
                </Field>
            </form>
        ),
        [assistant?.name, handleRename, submitted],
    );

    const renameAssistantButton = React.useCallback(
        (onRename?: (id: string, value: string) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="rename"
                disabled={!newName || submitted}
                onClick={() => handleRename(onRename, onError)}
                appearance="primary"
            >
                {submitted ? 'Renaming...' : 'Rename'}
            </Button>
        ),
        [handleRename, newName, submitted],
    );

    return { renameAssistantForm, renameAssistantButton };
};

interface AssistantRenameDialogProps {
    assistant?: Assistant;
    conversationId?: string;
    onRename?: (value: string) => Promise<void>;
    open?: boolean;
    onOpenChange?: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantRenameDialog: React.FC<AssistantRenameDialogProps> = (props) => {
    const { assistant, conversationId, onRename, open, onOpenChange } = props;
    const { renameAssistantForm, renameAssistantButton } = useAssistantRenameControls(assistant, conversationId);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'assistant-rename-error',
                title: 'Rename assistant failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Rename assistant"
            content={renameAssistantForm(onRename)}
            closeLabel="Cancel"
            additionalActions={[renameAssistantButton(onRename, handleError)]}
        />
    );
};

interface AssistantRenameProps {
    assistant: Assistant;
    conversationId?: string;
    disabled?: boolean;
    onRename?: (value: string) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantRename: React.FC<AssistantRenameProps> = (props) => {
    const { assistant, conversationId, disabled, onRename, iconOnly, asToolbarButton } = props;
    const { renameAssistantForm, renameAssistantButton } = useAssistantRenameControls(assistant, conversationId);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<EditRegular />}
            label="Rename"
            disabled={disabled}
            description="Rename assistant"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: `Rename assistant`,
                content: renameAssistantForm(onRename),
                closeLabel: 'Cancel',
                additionalActions: [renameAssistantButton(onRename)],
            }}
        />
    );
};
