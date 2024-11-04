// Copyright (c) Microsoft. All rights reserved.

import { Persona, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useAddConversationParticipantMutation, useCreateConversationMessageMutation } from '../../services/workbench';
import { AssistantAdd } from '../Assistants/AssistantAdd';
import { AssistantConfigure } from '../Assistants/AssistantConfigure';
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
    const { sortParticipants, getAvatarData } = useParticipantUtility();

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
                <div className={classes.participant} key={participant.id}>
                    <Persona
                        name={participant.name}
                        avatar={getAvatarData(participant)}
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
                        <div className={classes.actions}>
                            <AssistantConfigure
                                assistantId={participant.id}
                                disabled={readOnly || preventAssistantModifyOnParticipantIds.includes(participant.id)}
                            />
                            <AssistantRemove
                                conversation={conversation}
                                participant={participant}
                                disabled={readOnly || preventAssistantModifyOnParticipantIds.includes(participant.id)}
                            />
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
};
