// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Persona,
    makeStyles,
    tokens,
} from '@fluentui/react-components';
import { EditRegular, MoreHorizontalRegular, SettingsRegular } from '@fluentui/react-icons';
import React from 'react';
import { useParticipantUtility } from '../../libs/useParticipantUtility';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useGetAssistantQuery } from '../../services/workbench';
import { AssistantRemove } from '../Assistants/AssistantRemove';
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
    onConfigure?: (assistant: Assistant) => void;
    onRename?: (assistant: Assistant) => void;
}

export const ParticipantItem: React.FC<ParticipantItemProps> = (props) => {
    const { conversation, participant, readOnly, onConfigure, onRename } = props;
    const classes = useClasses();
    const { getAvatarData } = useParticipantUtility();

    const { data: assistant, error: assistantError } = useGetAssistantQuery(participant.id, {
        skip: participant.role !== 'assistant',
    });

    if (assistantError) {
        const errorMessage = JSON.stringify(assistantError);
        throw new Error(`Error loading assistant (${participant.id}): ${errorMessage}`);
    }

    const handleMenuItemClick = React.useCallback(
        (event: React.MouseEvent<HTMLDivElement>, handler?: (conversation: Conversation) => void) => {
            event.stopPropagation();
            handler?.(conversation);
        },
        [conversation],
    );

    const assistantActions = React.useMemo(() => {
        if (participant.role !== 'assistant' || !assistant || readOnly) {
            return null;
        }

        return (
            <Menu>
                <MenuTrigger disableButtonEnhancement>
                    <Button icon={<MoreHorizontalRegular />} />
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        {/* FIXME: complete the menu items */}
                        {onConfigure && (
                            <MenuItem
                                icon={<SettingsRegular />}
                                onClick={(event) => handleMenuItemClick(event, () => onConfigure(assistant))}
                            >
                                Configure
                            </MenuItem>
                        )}
                        {onRename && (
                            <MenuItem
                                icon={<EditRegular />}
                                onClick={(event) => handleMenuItemClick(event, () => onRename(assistant))}
                            >
                                Rename
                            </MenuItem>
                        )}
                        <AssistantServiceInfo assistant={assistant} simulateMenuItem />
                        <AssistantRemove conversation={conversation} participant={participant} simulateMenuItem />
                    </MenuList>
                </MenuPopover>
            </Menu>
        );
    }, [assistant, conversation, handleMenuItemClick, onConfigure, onRename, participant, readOnly]);

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
