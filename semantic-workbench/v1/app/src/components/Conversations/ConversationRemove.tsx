// Copyright (c) Microsoft. All rights reserved.

import { Button, DialogTrigger, Label } from '@fluentui/react-components';
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
}

export const ConversationRemove: React.FC<ConversationRemoveProps> = (props) => {
    const { conversation, onRemove, iconOnly, asToolbarButton, participantId } = props;
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
            label="Remove"
            dialogContent={{
                title: 'Remove Conversation',
                content: (
                    <>
                        <Label>Are you sure you want to remove this conversation from your list?</Label>
                    </>
                ),
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
