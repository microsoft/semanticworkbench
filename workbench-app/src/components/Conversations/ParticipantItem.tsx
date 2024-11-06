// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Menu,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { MoreHorizontalRegular } from '@fluentui/react-icons';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useGetAssistantQuery } from '../../services/workbench';
import { AssistantConfigure } from '../Assistants/AssistantConfigure';
import { AssistantRemove } from '../Assistants/AssistantRemove';
import { AssistantRename } from '../Assistants/AssistantRename';
import { AssistantServiceInfo } from '../Assistants/AssistantServiceInfo';

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

interface ParticipantItemProps {
    conversation: Conversation;
    participant: ConversationParticipant;
    readOnly?: boolean;
    preventAssistantModifyOnParticipantIds?: string[];
}

export const ParticipantItem: React.FC<ParticipantItemProps> = (props) => {
    const { conversation, participant, readOnly, preventAssistantModifyOnParticipantIds } = props;
    const classes = useClasses();
    const { getAvatarData } = useParticipantUtility();

    const { data: assistant, error: assistantError } = useGetAssistantQuery(participant.id, {
        skip: participant.role !== 'assistant',
    });

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant (${participant.id}): ${errorMessage}`);
    }

    const assistantActions = React.useMemo(() => {
        if (participant.role !== 'assistant') {
            return null;
        }

        return (
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button icon={<MoreHorizontalRegular />} />
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        {assistant && (
                            <>
                                <AssistantConfigure
                                    assistant={assistant}
                                    disabled={
                                        readOnly || preventAssistantModifyOnParticipantIds?.includes(participant.id)
                                    }
                                    simulateMenuItem
                                />
                                <AssistantRename
                                    assistant={assistant}
                                    conversationId={conversation.id}
                                    simulateMenuItem
                                />
                                <AssistantServiceInfo assistant={assistant} simulateMenuItem />
                            </>
                        )}
                        <AssistantRemove
                            conversation={conversation}
                            participant={participant}
                            disabled={readOnly || preventAssistantModifyOnParticipantIds?.includes(participant.id)}
                            simulateMenuItem
                        />
                    </MenuList>
                </MenuPopover>
            </Menu>
        );
    }, [assistant, conversation, participant, preventAssistantModifyOnParticipantIds, readOnly]);

    return (
        <div className={classes.participant} key={participant.id}>
            <Persona
                name={participant.name}
                avatar={getAvatarData(participant)}
                secondaryText={
                    participant.role + { read: ' (observer)', read_write: '' }[participant.conversationPermission]
                }
                presence={
                    participant.online === undefined
                        ? undefined
                        : {
                              status: participant.online ? 'available' : 'offline',
                          }
                }
            />
            {assistantActions}
        </div>
    );
};
