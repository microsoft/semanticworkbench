// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { PlugDisconnected24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useAppDispatch, useAppSelector } from '../../redux/app/hooks';
import { setActiveConversationId } from '../../redux/features/app/appSlice';
import { useRemoveConversationParticipantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';
import { DialogControl } from '../App/DialogControl';

const useConversationRemoveControls = () => {
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const dispatch = useAppDispatch();
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const [submitted, setSubmitted] = React.useState(false);

    const handleRemove = React.useCallback(
        async (conversationId: string, participantId: string, onRemove?: () => void) => {
            if (submitted) {
                return;
            }
            setSubmitted(true);

            try {
                if (activeConversationId === conversationId) {
                    // Clear the active conversation if it is the one being removed
                    dispatch(setActiveConversationId(undefined));
                }

                await removeConversationParticipant({
                    conversationId,
                    participantId,
                });
                onRemove?.();
            } finally {
                setSubmitted(false);
            }
        },
        [activeConversationId, dispatch, removeConversationParticipant, submitted],
    );

    const removeConversationForm = React.useCallback(
        () => <p>Are you sure you want to remove this conversation from your list?</p>,
        [],
    );

    const removeConversationButton = React.useCallback(
        (conversationId: string, participantId: string, onRemove?: () => void) => (
            <DialogTrigger disableButtonEnhancement>
                <Button
                    appearance="primary"
                    onClick={() => handleRemove(conversationId, participantId, onRemove)}
                    disabled={submitted}
                >
                    {submitted ? 'Removing...' : 'Remove'}
                </Button>
            </DialogTrigger>
        ),
        [handleRemove, submitted],
    );

    return {
        removeConversationForm,
        removeConversationButton,
    };
};

interface ConversationRemoveDialogProps {
    conversationId: string;
    participantId: string;
    onRemove: () => void;
    onCancel: () => void;
}

export const ConversationRemoveDialog: React.FC<ConversationRemoveDialogProps> = (props) => {
    const { conversationId, participantId, onRemove, onCancel } = props;
    const { removeConversationForm, removeConversationButton } = useConversationRemoveControls();

    return (
        <DialogControl
            open={true}
            onOpenChange={onCancel}
            title="Remove Conversation"
            content={removeConversationForm()}
            additionalActions={[removeConversationButton(conversationId, participantId, onRemove)]}
        />
    );
};

interface ConversationRemoveProps {
    conversation: Conversation;
    participantId: string;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationRemove: React.FC<ConversationRemoveProps> = (props) => {
    const { conversation, onRemove, iconOnly, asToolbarButton, participantId } = props;
    const { removeConversationForm, removeConversationButton } = useConversationRemoveControls();

    return (
        <CommandButton
            description="Remove Conversation"
            icon={<PlugDisconnected24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Remove"
            dialogContent={{
                title: 'Remove Conversation',
                content: removeConversationForm(),
                closeLabel: 'Cancel',
                additionalActions: [removeConversationButton(conversation.id, participantId, onRemove)],
            }}
        />
    );
};
