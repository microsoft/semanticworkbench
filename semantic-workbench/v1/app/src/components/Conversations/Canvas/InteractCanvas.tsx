// Copyright (c) Microsoft. All rights reserved.

import {
    DrawerHeader,
    DrawerHeaderTitle,
    InlineDrawer,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import debug from 'debug';
import React from 'react';
import { Constants } from '../../../Constants';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantCanvasList } from './AssistantCanvasList';
import { CanvasControls } from './CanvasControls';
import { ConversationCanvas } from './ConversationCanvas';

const log = debug(Constants.debug.root).extend('InteractCanvas');

const useClasses = makeStyles({
    root: {
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        flex: 1,
        height: '100%',
    },
    controls: {
        position: 'absolute',
        top: 0,
        right: 0,
    },
    drawer: {
        height: '100%',
        backgroundImage: `linear-gradient(to right, ${tokens.colorNeutralBackground1}, ${tokens.colorBrandBackground2})`,
    },
    drawerContent: {
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'auto',
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalM),
        boxSizing: 'border-box',
        '::-webkit-scrollbar-track': {
            backgroundColor: tokens.colorNeutralBackground1,
        },
        '::-webkit-scrollbar-thumb': {
            backgroundColor: tokens.colorNeutralStencil1Alpha,
        },
    },
});

interface InteractCanvasProps {
    conversationAssistants: Assistant[];
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
    preventAssistantModifyOnParticipantIds?: string[];
}

export const InteractCanvas: React.FC<InteractCanvasProps> = (props) => {
    const {
        conversationAssistants,
        conversationParticipants,
        conversationFiles,
        conversation,
        preventAssistantModifyOnParticipantIds,
    } = props;
    const classes = useClasses();
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const interactCanvasController = useInteractCanvasController();
    const [selectedAssistant, setSelectedAssistant] = React.useState<Assistant | null>(null);

    // Verify the selected assistant is in the conversation
    React.useEffect(() => {
        // If the assistant drawer is open, set to assistant mode, an assistant is selected,
        // and the assistant is not in the conversation, then close the assistant drawer
        if (
            interactCanvasState?.open &&
            interactCanvasState?.mode === 'assistant' &&
            interactCanvasState?.assistantId &&
            !conversationAssistants.some((assistant) => assistant.id === interactCanvasState.assistantId)
        ) {
            // Close the assistant drawer and reset the assistant state
            log('Assistant id is not in the conversation, closing assistant drawer and resetting assistant state');
            interactCanvasController.transitionToState({ open: false, assistantId: null, assistantStateId: null });
        }
    }, [conversationAssistants, interactCanvasState, interactCanvasController]);

    // If no assistant is selected, select the first assistant in the list if available
    React.useEffect(() => {
        // If an assistant is selected, do not change the selection
        if (interactCanvasState?.assistantId !== (null || undefined)) {
            return;
        }

        // If there are no assistants, do not select an assistant
        if (conversationAssistants.length === 0) {
            log('No assistants in the conversation');
            return;
        }

        // Select the first assistant in the list
        log('Selecting the first assistant in the conversation');
        interactCanvasController.setState({ assistantId: conversationAssistants[0].id });
    }, [conversationAssistants, interactCanvasState, interactCanvasController]);

    React.useEffect(() => {
        if (
            selectedAssistant?.id !== interactCanvasState?.assistantId &&
            interactCanvasState?.open &&
            interactCanvasState?.mode === 'assistant'
        ) {
            const assistant = conversationAssistants.find(
                (assistant) => assistant.id === interactCanvasState?.assistantId,
            );
            if (!assistant) {
                // If the selected assistant is not in the conversation, close the assistant drawer
                log(
                    'Selected assistant is not in the conversation, closing assistant drawer and resetting assistant state',
                );
                interactCanvasController.transitionToState({ open: false, assistantId: null, assistantStateId: null });
                return;
            }
            setSelectedAssistant(assistant);
        }
    }, [conversationAssistants, interactCanvasController, interactCanvasState, selectedAssistant]);

    // Determine which drawer to open, default to none
    let openDrawer: 'conversation' | 'assistant' | 'none' = 'none';
    if (interactCanvasState?.open) {
        // Open the conversation drawer if the mode is conversation
        if (interactCanvasState?.mode === 'conversation') {
            openDrawer = 'conversation';
        }

        // Open the assistant drawer if the mode is assistant and an assistant is selected
        if (interactCanvasState?.mode === 'assistant' && interactCanvasState?.assistantId !== (null || undefined)) {
            openDrawer = 'assistant';
        }

        // Otherwise do not open any drawer
    }

    return (
        <div className={classes.root}>
            <div className={classes.controls}>
                <CanvasControls conversationId={conversation.id} />
            </div>
            <InlineDrawer className={classes.drawer} open={openDrawer === 'conversation'} position="end" size="medium">
                <DrawerHeader>
                    <DrawerHeaderTitle>Conversation</DrawerHeaderTitle>
                </DrawerHeader>
                <div className={classes.drawerContent}>
                    <ConversationCanvas
                        conversation={conversation}
                        conversationParticipants={conversationParticipants}
                        conversationFiles={conversationFiles}
                        conversationAssistants={conversationAssistants}
                        preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                    />
                </div>
            </InlineDrawer>
            <InlineDrawer className={classes.drawer} open={openDrawer === 'assistant'} position="end" size="large">
                <DrawerHeader>
                    <DrawerHeaderTitle>Assistants</DrawerHeaderTitle>
                </DrawerHeader>
                <div className={classes.drawerContent}>
                    {selectedAssistant ? (
                        <AssistantCanvasList
                            selectedAssistant={selectedAssistant}
                            conversation={conversation}
                            conversationAssistants={conversationAssistants}
                        />
                    ) : (
                        'No assistant selected.'
                    )}
                </div>
            </InlineDrawer>
        </div>
    );
};
