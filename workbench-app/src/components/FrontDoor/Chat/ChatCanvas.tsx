// Copyright (c) Microsoft. All rights reserved.

import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { ConversationDrawer } from '../../Conversations/Canvas/ConversationDrawer';
import { AssistantDrawer } from './AssistantDrawer';

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
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const interactCanvasController = useInteractCanvasController();
    const [firstRun, setFirstRun] = React.useState(true);
    const [selectedAssistant, setSelectedAssistant] = React.useState<Assistant>();
    const [drawerMode, setDrawerMode] = React.useState<'inline' | 'overlay'>('inline');

    const onMediaQueryChange = React.useCallback(
        (matches: boolean) => setDrawerMode(matches ? 'overlay' : 'inline'),
        [setDrawerMode],
    );

    React.useEffect(() => {
        const mediaQuery = window.matchMedia(`(max-width: ${Constants.app.responsiveBreakpoints.interactCanvas})`);

        if (mediaQuery.matches) {
            setDrawerMode('overlay');
        }

        mediaQuery.addEventListener('change', (event) => onMediaQueryChange(event.matches));

        return () => {
            mediaQuery.removeEventListener('change', (event) => onMediaQueryChange(event.matches));
        };
    }, [onMediaQueryChange]);

    // Set the selected assistant based on the interact canvas state
    React.useEffect(() => {
        if (
            !interactCanvasState?.assistantId ||
            !interactCanvasState?.open ||
            interactCanvasState?.mode !== 'assistant'
        ) {
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
                interactCanvasController.transitionToState({ open: true, mode: 'conversation' });
                setFirstRun(false);
            }
            return;
        }

        // Find the assistant that corresponds to the selected assistant id
        const assistant = conversationAssistants.find((assistant) => assistant.id === interactCanvasState?.assistantId);

        // If the selected assistant is not found in the conversation, select the first assistant in the conversation
        if (!assistant) {
            log('Selected assistant not found in conversation, selecting the first assistant in the conversation');
            interactCanvasController.setState({ assistantId: conversationAssistants[0].id });
            return;
        }

        // If the requested assistant is different from the selected assistant, set the selected assistant
        if (selectedAssistant?.id !== assistant?.id) {
            log(`Setting selected assistant to ${assistant.id}`);
            setSelectedAssistant(assistant);
        }
    }, [conversationAssistants, firstRun, interactCanvasController, interactCanvasState, selectedAssistant]);

    // Determine which drawer to open, default to none
    let openDrawer: 'conversation' | 'assistant' | 'none' = 'none';
    if (interactCanvasState?.open) {
        // Open the conversation drawer if the mode is conversation
        if (interactCanvasState?.mode === 'conversation') {
            openDrawer = 'conversation';
        }

        // Open the assistant drawer if the mode is assistant
        if (interactCanvasState?.mode === 'assistant') {
            openDrawer = 'assistant';
        }

        // Otherwise do not open any drawer
    }

    return (
        <>
            <ConversationDrawer
                open={openDrawer === 'conversation'}
                mode={drawerMode}
                readOnly={readOnly}
                conversation={conversation}
                conversationParticipants={conversationParticipants}
                conversationFiles={conversationFiles}
                preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
            />
            <AssistantDrawer
                open={openDrawer === 'assistant'}
                mode={drawerMode}
                conversation={conversation}
                conversationAssistants={conversationAssistants}
                selectedAssistant={selectedAssistant}
            />
        </>
    );
};
