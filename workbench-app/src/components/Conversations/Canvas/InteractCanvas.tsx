// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, mergeClasses, shorthands, tokens } from '@fluentui/react-components';
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
import { CanvasDrawer } from './CanvasDrawer';
import { ConversationCanvas } from './ConversationCanvas';

const log = debug(Constants.debug.root).extend('InteractCanvas');

const useClasses = makeStyles({
    controls: {
        position: 'relative',
        top: 0,
        right: 0,
        zIndex: tokens.zIndexFloating,
    },
    controlsInline: {
        position: 'absolute',
    },
    controlsOverlay: {
        position: 'fixed',
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
    drawerOpenInlineNarrow: {
        width: 'min(50vw, 500px)',
    },
    drawerOpenInlineWide: {
        width: 'calc(200vw - 300px)',
    },
    drawerOpenOverlay: {
        width: '100%',
    },
});

const drawerResponsiveBreakpoint = '900px';

interface InteractCanvasProps {
    conversationAssistants: Assistant[];
    conversationParticipants: ConversationParticipant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
    preventAssistantModifyOnParticipantIds?: string[];
    readOnly: boolean;
}

export const InteractCanvas: React.FC<InteractCanvasProps> = (props) => {
    const {
        conversationAssistants,
        conversationParticipants,
        conversationFiles,
        conversation,
        preventAssistantModifyOnParticipantIds,
        readOnly,
    } = props;
    const classes = useClasses();
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const interactCanvasController = useInteractCanvasController();
    const [firstRun, setFirstRun] = React.useState(true);
    const [selectedAssistant, setSelectedAssistant] = React.useState<Assistant | null>(null);
    const [drawerMode, setDrawerMode] = React.useState<'inline' | 'overlay'>('inline');

    const onMediaQueryChange = React.useCallback(
        (matches: boolean) => setDrawerMode(matches ? 'overlay' : 'inline'),
        [setDrawerMode],
    );

    React.useEffect(() => {
        const mediaQuery = window.matchMedia(`(max-width: ${drawerResponsiveBreakpoint})`);

        if (mediaQuery.matches) {
            setDrawerMode('overlay');
        }

        mediaQuery.addEventListener('change', (event) => onMediaQueryChange(event.matches));

        return () => {
            mediaQuery.removeEventListener('change', (event) => onMediaQueryChange(event.matches));
        };
    }, [onMediaQueryChange]);

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
        if (interactCanvasState?.assistantId) {
            return;
        }

        // If there are no assistants, do not select an assistant
        if (conversationAssistants.length === 0) {
            log('No assistants in the conversation');

            // If this is the first run, transition to the conversation mode to add an assistant
            if (firstRun) {
                interactCanvasController.transitionToState({ open: true, mode: 'conversation' });
                setFirstRun(false);
            }
            return;
        }

        // Select the first assistant in the list
        log('Selecting the first assistant in the conversation');
        interactCanvasController.setState({ assistantId: conversationAssistants[0].id });
    }, [conversationAssistants, interactCanvasState, interactCanvasController, firstRun]);

    // Set the selected assistant when the assistant id changes and the canvas is open and in assistant mode
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
        if (interactCanvasState?.mode === 'assistant' && interactCanvasState?.assistantId) {
            openDrawer = 'assistant';
        }

        // Otherwise do not open any drawer
    }

    const controlsClassName = mergeClasses(
        classes.controls,
        openDrawer !== 'none' && drawerMode === 'overlay' ? classes.controlsOverlay : classes.controlsInline,
    );

    return (
        <>
            <div className={controlsClassName}>
                <CanvasControls conversationId={conversation.id} />
            </div>
            <CanvasDrawer
                openClassName={drawerMode === 'inline' ? classes.drawerOpenInlineNarrow : classes.drawerOpenOverlay}
                className={classes.drawer}
                open={openDrawer === 'conversation'}
                mode={drawerMode}
                side="right"
                title="Conversation"
            >
                <ConversationCanvas
                    readOnly={readOnly}
                    conversation={conversation}
                    conversationParticipants={conversationParticipants}
                    conversationFiles={conversationFiles}
                    conversationAssistants={conversationAssistants}
                    preventAssistantModifyOnParticipantIds={preventAssistantModifyOnParticipantIds}
                />
            </CanvasDrawer>
            <CanvasDrawer
                openClassName={drawerMode === 'inline' ? classes.drawerOpenInlineWide : classes.drawerOpenOverlay}
                className={classes.drawer}
                open={openDrawer === 'assistant'}
                mode={drawerMode}
                side="right"
                title="Assistants"
            >
                {selectedAssistant ? (
                    <AssistantCanvasList
                        selectedAssistant={selectedAssistant}
                        conversation={conversation}
                        conversationAssistants={conversationAssistants}
                    />
                ) : (
                    'No assistant selected.'
                )}
            </CanvasDrawer>
        </>
    );
};
