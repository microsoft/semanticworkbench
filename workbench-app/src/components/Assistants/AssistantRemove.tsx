// Copyright (c) Microsoft. All rights reserved.

import { DialogTrigger } from '@fluentui/react-components';
import { PlugDisconnectedRegular } from '@fluentui/react-icons';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import {
    useCreateConversationMessageMutation,
    useRemoveConversationParticipantMutation,
} from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

interface AssistantRemoveProps {
    participant: ConversationParticipant;
    conversation: Conversation;
    disabled?: boolean;
}

export const AssistantRemove: React.FC<AssistantRemoveProps> = (props) => {
    const { participant, conversation, disabled } = props;
    const [removeConversationParticipant] = useRemoveConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();

    const handleAssistantRemove = async () => {
        await removeConversationParticipant({
            conversationId: conversation.id,
            participantId: participant.id,
        });

        const content = `${participant.name} removed from conversation`;

        await createConversationMessage({
            conversationId: conversation.id,
            content,
            messageType: 'notice',
        });
    };

    return (
        <CommandButton
            icon={<PlugDisconnectedRegular />}
            iconOnly
            disabled={disabled}
            description={disabled ? `Workflow assistants cannot be removed` : 'Remove assistant from conversation'}
            dialogContent={{
                title: `Remove "${participant.name}"`,
                content: (
                    <p>
                        Are you sure you want to remove assistant <strong>{participant.name}</strong> from this
                        conversation?
                    </p>
                ),
                closeLabel: 'Cancel',
                additionalActions: [
                    <DialogTrigger key="remove" disableButtonEnhancement>
                        <CommandButton
                            icon={<PlugDisconnectedRegular />}
                            label="Remove"
                            onClick={handleAssistantRemove}
                        />
                    </DialogTrigger>,
                ],
            }}
        />
    );
};
