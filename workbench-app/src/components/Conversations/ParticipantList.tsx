// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAddConversationParticipantMutation, useCreateConversationMessageMutation } from '../../services/workbench';
import { AssistantAdd } from '../Assistants/AssistantAdd';
import { ParticipantItem } from './ParticipantItem';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
    },
    participant: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
    },
    actions: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalS,
    },
});

interface ParticipantListProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    preventAssistantModifyOnParticipantIds?: string[];
    readOnly: boolean;
}

export const ParticipantList: React.FC<ParticipantListProps> = (props) => {
    const { conversation, participants, preventAssistantModifyOnParticipantIds = [], readOnly } = props;
    const classes = useClasses();

    const { sortParticipants } = useParticipantUtility();

    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();

    const handleAssistantAdd = async (assistant: Assistant) => {
        // send notice message first, to announce before assistant reacts to create event
        await createConversationMessage({
            conversationId: conversation.id,
            content: `${assistant.name} added to conversation`,
            messageType: 'notice',
        });

        await addConversationParticipant({
            conversationId: conversation.id,
            participantId: assistant.id,
        });
    };

    const exceptAssistantIds = participants
        .filter((participant) => participant.active && participant.role === 'assistant')
        .map((participant) => participant.id);

    return (
        <div className={classes.root}>
            <AssistantAdd disabled={readOnly} exceptAssistantIds={exceptAssistantIds} onAdd={handleAssistantAdd} />
            {sortParticipants(participants).map((participant) => (
                <ParticipantItem
                    key={participant.id}
                    conversation={conversation}
                    participant={participant}
                    readOnly={readOnly}
                    preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                />
            ))}
        </div>
    );
};
