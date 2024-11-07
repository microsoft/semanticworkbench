import React from 'react';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { ConversationCanvas } from '../../Conversations/Canvas/ConversationCanvas';
import { CanvasDrawer, CanvasDrawerOptions } from './CanvasDrawer';

interface ConversationDrawerProps {
    drawerOptions: CanvasDrawerOptions;
    readOnly: boolean;
    conversation: Conversation;
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    preventAssistantModifyOnParticipantIds?: string[];
}

export const ConversationDrawer: React.FC<ConversationDrawerProps> = (props) => {
    const {
        drawerOptions,
        readOnly,
        conversation,
        conversationParticipants,
        conversationFiles,
        preventAssistantModifyOnParticipantIds,
    } = props;

    const options: CanvasDrawerOptions = React.useMemo(
        () => ({
            ...drawerOptions,
            size: 'small',
        }),
        [drawerOptions],
    );

    return (
        <CanvasDrawer options={options}>
            <ConversationCanvas
                readOnly={readOnly}
                conversation={conversation}
                conversationParticipants={conversationParticipants}
                conversationFiles={conversationFiles}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
        </CanvasDrawer>
    );
};
