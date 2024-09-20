// Copyright (c) Microsoft. All rights reserved.

import { Card, Text, makeStyles, tokens } from '@fluentui/react-components';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ConversationTranscript } from '../ConversationTranscript';
import { FileList } from '../FileList';
import { ParticipantList } from '../ParticipantList';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingHorizontalM,
        width: '100%',
    },
    card: {
        overflow: 'visible',
    },
});

interface ConversationCanvasProps {
    conversationAssistants: Assistant[];
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
    preventAssistantModifyOnParticipantIds?: string[];
}

export const ConversationCanvas: React.FC<ConversationCanvasProps> = (props) => {
    const { conversationParticipants, conversationFiles, conversation, preventAssistantModifyOnParticipantIds } = props;
    const classes = useClasses();

    return (
        <div className={classes.root}>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Participants
                </Text>
                <ParticipantList
                    conversation={conversation}
                    participants={conversationParticipants}
                    preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                />
            </Card>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Transcript
                </Text>
                <ConversationTranscript conversation={conversation} participants={conversationParticipants} />
            </Card>
            <Card className={classes.card}>
                <Text size={400} weight="semibold">
                    Files
                </Text>
                <FileList conversation={conversation} conversationFiles={conversationFiles} />
            </Card>
        </div>
    );
};
