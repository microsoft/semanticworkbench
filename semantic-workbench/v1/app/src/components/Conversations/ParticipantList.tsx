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
    readOnly: boolean;
}

export const ParticipantList: React.FC<ParticipantListProps> = (props) => {
    const { conversation, participants, preventAssistantModifyOnParticipantIds = [], readOnly } = props;
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

    const onlineParticipants = participants
        .filter((participant) => participant.active)
        .toSorted((a, b) => a.name.localeCompare(b.name));

    return (
        <div className={classes.root}>
            <AssistantAdd disabled={readOnly} exceptAssistantIds={exceptAssistantIds} onAdd={handleAssistantAdd} />
            {onlineParticipants.map((participant) => (
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
                        secondaryText={
                            participant.role +
                            { read: ' (observer)', read_write: '' }[participant.conversationPermission]
                        }
                        presence={
                            participant.online === undefined
                                ? undefined
                                : {
                                      status: participant.online ? 'available' : 'offline',
                                  }
                        }
                    />
                    {participant.role === 'assistant' && (
                        <AssistantRemove
                            conversation={conversation}
                            participant={participant}
                            disabled={readOnly || preventAssistantModifyOnParticipantIds.includes(participant.id)}
                        />
                    )}
                </div>
            ))}
        </div>
    );
};
