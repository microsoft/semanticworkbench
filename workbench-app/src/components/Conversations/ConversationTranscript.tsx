// Copyright (c) Microsoft. All rights reserved.

import { ArrowDownload24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useWorkbenchService } from '../../libs/useWorkbenchService';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { CommandButton } from '../App/CommandButton';

interface ConversationTranscriptProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    iconOnly?: boolean;
    asToolbarButton?: boolean;
}

export const ConversationTranscript: React.FC<ConversationTranscriptProps> = (props) => {
    const { conversation, participants, iconOnly, asToolbarButton } = props;
    const workbenchService = useWorkbenchService();
    const [submitted, setSubmitted] = React.useState(false);

    const getTranscript = React.useCallback(async () => {
        if (submitted) {
            return;
        }
        setSubmitted(true);

        try {
            const { blob, filename } = await workbenchService.exportTranscriptAsync(conversation, participants);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
        } finally {
            setSubmitted(false);
        }
    }, [submitted, workbenchService, conversation, participants]);

    return (
        <div>
            <CommandButton
                description={`Download transcript`}
                icon={<ArrowDownload24Regular />}
                iconOnly={iconOnly}
                asToolbarButton={asToolbarButton}
                disabled={submitted}
                label={submitted ? 'Downloading...' : 'Download'}
                onClick={getTranscript}
            />
        </div>
    );
};
