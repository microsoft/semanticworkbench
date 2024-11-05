// Copyright (c) Microsoft. All rights reserved.

import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantDrawer } from './AssistantDrawer';
import { ConversationDrawer } from './ConversationDrawer';

const log = debug(Constants.debug.root).extend('ChatCanvas');

interface ChatCanvasProps {
    conversationAssistants?: Assistant[];
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
    preventAssistantModifyOnParticipantIds?: string[];
    readOnly: boolean;
}

export const ChatCanvas: React.FC<ChatCanvasProps> = (props) => {
    const {
        conversationAssistants,
        conversationParticipants,
        conversationFiles,
        conversation,
        preventAssistantModifyOnParticipantIds,
        readOnly,
    } = props;
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const chatCanvasController = useChatCanvasController();
    const [firstRun, setFirstRun] = React.useState(true);
    const [selectedAssistant, setSelectedAssistant] = React.useState<Assistant>();

    // Set the selected assistant based on the chat canvas state
    React.useEffect(() => {
        if (!chatCanvasState.selectedAssistantId || !chatCanvasState.open || chatCanvasState.mode !== 'assistant') {
            // If the assistant id is not set, the canvas is closed, or the mode is not assistant, clear
            // the selected assistant and exit early
            setSelectedAssistant(undefined);
            return;
        }

        // If no assistants are in the conversation, unset the selected assistant
        if (!conversationAssistants || conversationAssistants.length === 0) {
            if (selectedAssistant) setSelectedAssistant(undefined);
            // If this is the first run, transition to the conversation mode to add an assistant
            if (firstRun) {
                log('No assistants in the conversation on first run, transitioning to conversation mode');
                chatCanvasController.transitionToState({ open: true, mode: 'conversation' });
                setFirstRun(false);
            }
            return;
        }

        // Find the assistant that corresponds to the selected assistant id
        const assistant = conversationAssistants.find(
            (assistant) => assistant.id === chatCanvasState.selectedAssistantId,
        );

        // If the selected assistant is not found in the conversation, select the first assistant in the conversation
        if (!assistant) {
            log('Selected assistant not found in conversation, selecting the first assistant in the conversation');
            chatCanvasController.setState({ selectedAssistantId: conversationAssistants[0].id });
            return;
        }

        // If the requested assistant is different from the selected assistant, set the selected assistant
        if (selectedAssistant?.id !== assistant?.id) {
            log(`Setting selected assistant to ${assistant.id}`);
            setSelectedAssistant(assistant);
        }
    }, [
        conversationAssistants,
        chatCanvasController,
        selectedAssistant,
        firstRun,
        chatCanvasState.selectedAssistantId,
        chatCanvasState.open,
        chatCanvasState.mode,
    ]);

    // Determine which drawer to open, default to none
    const openDrawer = chatCanvasState.open ? chatCanvasState.mode : 'none';
    return (
        <>
            <ConversationDrawer
                drawerOptions={{
                    open: openDrawer === 'conversation',
                }}
                readOnly={readOnly}
                conversation={conversation}
                conversationParticipants={conversationParticipants}
                conversationFiles={conversationFiles}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
            <AssistantDrawer
                drawerOptions={{
                    open: openDrawer === 'assistant',
                }}
                conversation={conversation}
                conversationAssistants={conversationAssistants}
                selectedAssistant={selectedAssistant}
            />
        </>
    );
};
