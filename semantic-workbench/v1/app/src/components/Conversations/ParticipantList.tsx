// Copyright (c) Microsoft. All rights reserved.

import { Persona, makeStyles, tokens } from '@fluentui/react-components';
import { AppGenericRegular, BotRegular, PersonRegular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAddConversationParticipantMutation, useCreateConversationMessageMutation } from '../../services/workbench';
import { AssistantAdd } from '../Assistants/AssistantAdd';
import { AssistantRemove } from '../Assistants/AssistantRemove';

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
});

interface ParticipantListProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    preventAssistantModifyOnParticipantIds?: string[];
}

export const ParticipantList: React.FC<ParticipantListProps> = (props) => {
    const { conversation, participants, preventAssistantModifyOnParticipantIds = [] } = props;
    const classes = useClasses();

    const [addConversationParticipant] = useAddConversationParticipantMutation();
    const [createConversationMessage] = useCreateConversationMessageMutation();

    const handleAssistantAdd = async (assistant: Assistant) => {
        await addConversationParticipant({
            conversationId: conversation.id,
            participantId: assistant.id,
        });

        await createConversationMessage({
            conversationId: conversation.id,
            content: `${assistant.name} added to conversation`,
            messageType: 'notice',
        });
    };

    const exceptAssistantIds = participants
        .filter((participant) => participant.active && participant.role === 'assistant')
        .map((participant) => participant.id);

    return (
        <div className={classes.root}>
            <AssistantAdd exceptAssistantIds={exceptAssistantIds} onAdd={handleAssistantAdd} />
            {participants
                .filter((participant) => participant.active)
                .toSorted((a, b) => a.name.localeCompare(b.name))
                .map((participant) => (
                    <div className={classes.participant} key={participant.id}>
                        <Persona
                            name={participant.name}
                            avatar={{
                                name: '',
                                icon: {
                                    user: <PersonRegular />,
                                    assistant: <BotRegular />,
                                    service: <AppGenericRegular />,
                                }[participant.role],
                            }}
                            secondaryText={participant.role}
                            presence={
                                participant.online === undefined
                                    ? null
                                    : {
                                          status: participant.online ? 'available' : 'offline',
                                      }
                            }
                        />
                        {participant.role === 'assistant' && (
                            <AssistantRemove
                                conversation={conversation}
                                participant={participant}
                                disabled={preventAssistantModifyOnParticipantIds.includes(participant.id)}
                            />
                        )}
                    </div>
                ))}
        </div>
    );
};
