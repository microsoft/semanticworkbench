// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Utility } from '../../libs/Utility';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useGetConversationMessagesQuery } from '../../services/workbench';
import { CommandButton } from '../App/CommandButton';

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

        const timestampForFilename = Utility.getTimestampForFilename();
        const filename = `transcript_${conversation.title.replaceAll(' ', '_')}_${timestampForFilename}.md`;

        const markdown = messages
            .filter((message) => message.messageType !== 'log')
            .map((message) => {
                const date = Utility.toFormattedDateString(message.timestamp, 'dddd, MMMM D');
                const time = Utility.toFormattedDateString(message.timestamp, 'h:mm A');
                const participant = participants.find(
                    (possible_participant) => possible_participant.id === message.sender.participantId,
                );
                const sender = participant ? participant.name : 'Unknown';
                const parts = [];
                parts.push(`### [${date} ${time}] ${sender}:`);
                if (message.messageType !== 'chat') {
                    parts.push(`${message.messageType}: ${message.content}`);
                } else {
                    parts.push(message.content);
                }
                if (message.filenames && message.filenames.length > 0) {
                    parts.push(
                        message.filenames
                            .map((filename) => {
                                return `attachment: ${filename}`;
                            })
                            .join('\n'),
                    );
                }
                parts.push('----------------------------------\n\n');

                return parts.join('\n\n');
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
