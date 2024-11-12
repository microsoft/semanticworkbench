// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogOpenChangeData, DialogOpenChangeEvent } from '@fluentui/react-components';
import { PlugDisconnectedRegular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { useNotify } from '../../libs/useNotify';
import { Assistant } from '../../models/Assistant';
import {
    useCreateConversationMessageMutation,
    useGetConversationParticipantsQuery,
    useRemoveConversationParticipantMutation,
} from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useAssistantRemoveControls = (assistant?: Assistant, conversationId?: string) => {
    const [createConversationMessage] = useCreateConversationMessageMutation();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const { refetch: refetchParticipants } = useGetConversationParticipantsQuery(conversationId ?? '', {
        skip: !conversationId,
    });
    const [submitted, setSubmitted] = React.useState(false);

    const handleRemove = React.useCallback(
        async (onRemove?: (assistant: Assistant) => Promise<void>, onError?: (error: Error) => void) => {
            if (!assistant || !conversationId || submitted) {
                return;
            }

            try {
                await Utility.withStatus(setSubmitted, async () => {
                    await removeConversationParticipant({
                        conversationId: conversationId,
                        participantId: assistant.id,
                    });
                    await onRemove?.(assistant);

                    const content = `${assistant.name} removed from conversation`;
                    await createConversationMessage({
                        conversationId: conversationId,
                        content,
                        messageType: 'notice',
                    });

                    // Refetch participants to update the assistant name in the list
                    if (conversationId) {
                        await refetchParticipants();
                    }
                });
            } catch (error) {
                onError?.(error as Error);
            }
        },
        [
            assistant,
            conversationId,
            createConversationMessage,
            refetchParticipants,
            removeConversationParticipant,
            submitted,
        ],
    );

    const removeAssistantForm = React.useCallback(
        (onRemove?: (assistant: Assistant) => Promise<void>) => (
            <form
                onSubmit={(event) => {
                    event.preventDefault();
                    handleRemove(onRemove);
                }}
            >
                <p>
                    Are you sure you want to remove assistant <strong>{assistant?.name}</strong> from this conversation?
                </p>
            </form>
        ),
        [assistant?.name, handleRemove],
    );

    const removeAssistantButton = React.useCallback(
        (onRemove?: (assistant: Assistant) => Promise<void>, onError?: (error: Error) => void) => (
            <Button
                key="remove"
                disabled={submitted}
                onClick={() => handleRemove(onRemove, onError)}
                appearance="primary"
            >
                {submitted ? 'Removing...' : 'Remove'}
            </Button>
        ),
        [handleRemove, submitted],
    );

    return {
        removeAssistantForm,
        removeAssistantButton,
    };
};

interface AssistantRemoveDialogProps {
    assistant?: Assistant;
    conversationId?: string;
    onRemove?: (assistant: Assistant) => Promise<void>;
    open: boolean;
    onOpenChange: (event: DialogOpenChangeEvent, data: DialogOpenChangeData) => void;
}

export const AssistantRemoveDialog: React.FC<AssistantRemoveDialogProps> = (props) => {
    const { assistant, conversationId, open, onOpenChange, onRemove } = props;
    const { removeAssistantForm, removeAssistantButton } = useAssistantRemoveControls(assistant, conversationId);
    const { notifyWarning } = useNotify();

    const handleError = React.useCallback(
        (error: Error) => {
            notifyWarning({
                id: 'assistant-remove-error',
                title: 'Remove assistant failed',
                message: error.message,
            });
        },
        [notifyWarning],
    );

    return (
        <DialogControl
            open={open}
            onOpenChange={onOpenChange}
            title="Remove assistant"
            content={removeAssistantForm(onRemove)}
            closeLabel="Cancel"
            additionalActions={[removeAssistantButton(onRemove, handleError)]}
        />
    );
};

interface AssistantRemoveProps {
    assistant: Assistant;
    conversationId: string;
    disabled?: boolean;
    onRemove?: (assistant: Assistant) => Promise<void>;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const AssistantRemove: React.FC<AssistantRemoveProps> = (props) => {
    const { assistant, conversationId, disabled, onRemove, iconOnly, asToolbarButton } = props;
    const { removeAssistantForm, removeAssistantButton } = useAssistantRemoveControls(assistant, conversationId);

    return (
        <CommandButton
            iconOnly={iconOnly}
            icon={<PlugDisconnectedRegular />}
            label="Remove"
            disabled={disabled}
            description="Remove assistant"
            asToolbarButton={asToolbarButton}
            dialogContent={{
                title: `Remove "${assistant.name}"`,
                content: removeAssistantForm(onRemove),
                closeLabel: 'Cancel',
                additionalActions: [removeAssistantButton(onRemove)],
            }}
        />
    );
};
