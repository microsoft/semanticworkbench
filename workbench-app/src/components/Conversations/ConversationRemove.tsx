// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger } from '@fluentui/react-components';
import { PlugDisconnected24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { useRemoveConversationParticipantMutation } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface ConversationRemoveProps {
    conversation: Conversation;
    participantId: string;
    onRemove?: () => void;
    iconOnly?: boolean;
    asToolbarButton?: boolean;
    asMenuItem?: boolean;
}

export const ConversationRemove: React.FC<ConversationRemoveProps> = (props) => {
    const { conversation, onRemove, iconOnly, asToolbarButton, asMenuItem, participantId } = props;
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();

    const handleRemove = React.useCallback(async () => {
        await removeConversationParticipant({
            conversationId: conversation.id,
            participantId: participantId,
        });
        onRemove?.();
    }, [conversation.id, participantId, onRemove, removeConversationParticipant]);

    return (
        <CommandButton
            description="Remove Conversation"
            icon={<PlugDisconnected24Regular />}
            iconOnly={iconOnly}
            asToolbarButton={asToolbarButton}
            asMenuItem={asMenuItem}
            label="Remove"
            dialogContent={{
                title: 'Remove Conversation',
                content: <p>Are you sure you want to remove this conversation from your list?</p>,
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="delete">
                        <Button appearance="primary" onClick={handleRemove}>
                            Remove
                        </Button>
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
