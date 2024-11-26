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
        async (conversations: Conversation[], participantId: string, onRemove?: () => void) => {
            if (submitted) {
                return;
            }
            setSubmitted(true);

            try {
                for (const conversation of conversations) {
                    const conversationId = conversation.id;
                    if (activeConversationId === conversationId) {
                        // Clear the active conversation if it is the one being removed
                        dispatch(setActiveConversationId(undefined));
                    }

                    await removeConversationParticipant({
                        conversationId,
                        participantId,
                    });
                }
                onRemove?.();
            } finally {
                setSubmitted(false);
            }
        },
        [activeConversationId, dispatch, removeConversationParticipant, submitted],
    );

    const removeConversationForm = React.useCallback(
        (hasMultipleConversations: boolean) =>
            hasMultipleConversations ? (
                <p>Are you sure you want to remove these conversations from your list ?</p>
            ) : (
                <p>Are you sure you want to remove this conversation from your list ?</p>
            ),
        [],
    );

    const removeConversationButton = React.useCallback(
        (conversations: Conversation[], participantId: string, onRemove?: () => void) => (
            <DialogTrigger disableButtonEnhancement>
                <Button
                    appearance="primary"
                    onClick={() => handleRemove(conversations, participantId, onRemove)}
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
    conversations: Conversation | Conversation[];
    participantId: string;
    onRemove: () => void;
    onCancel: () => void;
}

export const ConversationRemoveDialog: React.FC<ConversationRemoveDialogProps> = (props) => {
    const { conversations, participantId, onRemove, onCancel } = props;
    const { removeConversationForm, removeConversationButton } = useConversationRemoveControls();

    const hasMultipleConversations = Array.isArray(conversations);
    const conversationsToRemove = hasMultipleConversations ? conversations : [conversations];

    return (
        <DialogControl
            open={true}
            onOpenChange={onCancel}
            title={hasMultipleConversations ? 'Remove Conversations' : 'Remove Conversation'}
            content={removeConversationForm(hasMultipleConversations)}
            additionalActions={[removeConversationButton(conversationsToRemove, participantId, onRemove)]}
        />
    );
};

interface ConversationRemoveProps {
    conversations: Conversation | Conversation[];
    participantId: string;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationRemove: React.FC<ConversationRemoveProps> = (props) => {
    const { conversations, onRemove, iconOnly, asToolbarButton, participantId } = props;
    const { removeConversationForm, removeConversationButton } = useConversationRemoveControls();

    const hasMultipleConversations = Array.isArray(conversations);
    const conversationsToRemove = hasMultipleConversations ? conversations : [conversations];
    const description = hasMultipleConversations ? 'Remove Conversations' : 'Remove Conversation';

    return (
        <CommandButton
            description={description}
            icon={<PlugDisconnected24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            label="Remove"
            dialogContent={{
                title: description,
                content: removeConversationForm(hasMultipleConversations),
                closeLabel: 'Cancel',
                additionalActions: [removeConversationButton(conversationsToRemove, participantId, onRemove)],
            }}
        />
    );
};
