// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useGetConversationMessagesQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

interface ConversationTranscriptProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationTranscript: React.FC<ConversationTranscriptProps> = (props) => {
    const { conversation, participants, iconOnly, asToolbarButton } = props;
    const {
        data: messages,
        error: messagesError,
        isLoading: isLoadingMessages,
    } = useGetConversationMessagesQuery(conversation.id);

    if (messagesError) {
        const errorMessage = JSON.stringify(messagesError);
        throw new Error(`Error loading messages: ${errorMessage}`);
    }

    const getTranscript = async () => {
        if (!messages) {
            return;
        }

        const currentDateTime = dayjs.utc().tz(dayjs.tz.guess()).format('YYYYMMDDHHmmss');
        const filename = `transcript_${conversation.title.replaceAll(' ', '_')}_${currentDateTime}.md`;

        const markdown = messages
            .filter((message) => message.messageType !== 'log')
            .map((message) => {
                const date = dayjs.utc(message.timestamp).tz(dayjs.tz.guess()).format('dddd, MMMM D');
                const time = dayjs.utc(message.timestamp).tz(dayjs.tz.guess()).format('h:mm A');
                const participant = participants.find(
                    (possible_participant) => possible_participant.id === message.sender.participantId,
                );
                const sender = participant ? participant.name : 'Unknown';
                return `### [${date} ${time}] ${sender}:\n\n${message.content}\n\n---\n\n`;
            })
            .join('\n');

        const blob = new Blob([markdown], { type: 'text/markdown' });

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div>
            <CommandButton
                disabled={isLoadingMessages || !messages}
                description={`Download transcript`}
                icon={<ArrowDownload24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                label="Download"
                onClick={getTranscript}
            />
        </div>
    );
};
