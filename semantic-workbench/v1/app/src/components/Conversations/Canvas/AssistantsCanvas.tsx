// Copyright (c) Microsoft. All rights reserved.

import { Button, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import React from 'react';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { AssistantCanvas } from './AssistantCanvas';

const useClasses = makeStyles({
    noAssistants: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        ...shorthands.padding(tokens.spacingVerticalS),
    },
    headerContent: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalM,
        ...shorthands.padding(tokens.spacingVerticalS),
    },
});

interface AssistantsCanvasProps {
    conversationAssistants: Assistant[];
    conversation: Conversation;
}

export const AssistantsCanvas: React.FC<AssistantsCanvasProps> = (props) => {
    const { conversationAssistants, conversation } = props;
    const classes = useClasses();
    const { interactCanvasState } = useAppSelector((state) => state.app);
    const interactCanvasController = useInteractCanvasController();

    React.useEffect(() => {
        if (conversationAssistants.length === 0) {
            if (interactCanvasState?.assistantId) {
                interactCanvasController.transitionToState({ assistantId: null });
            }
            return;
        }

        // Verify the selected assistant is still in the list
        if (
            interactCanvasState?.assistantId &&
            conversationAssistants.some((assistant) => assistant.id === interactCanvasState.assistantId)
        ) {
            // Assistant is still in the list
            return;
        }

        // Select the first assistant in the list
        interactCanvasController.transitionToState({ assistantId: conversationAssistants[0].id });
    }, [conversationAssistants, interactCanvasState, interactCanvasController]);

    const selectedAssistant = conversationAssistants.find(
        (assistant) => assistant.id === interactCanvasState?.assistantId,
    );

    return (
        <>
            {conversationAssistants.length === 0 && (
                <div className={classes.noAssistants}>
                    No assistants found.
                    <Button
                        appearance="secondary"
                        onClick={() => interactCanvasController.transitionToState({ open: false })}
                        icon={<BookInformation24Regular />}
                    />
                </div>
            )}
            {conversationAssistants.length === 1 && selectedAssistant && (
                <AssistantCanvas assistant={selectedAssistant} conversationId={conversation.id} />
            )}
            {conversationAssistants.length > 1 && (
                <>
                    <div className={classes.headerContent}>
                        <TabList
                            selectedValue={selectedAssistant?.id ?? conversationAssistants[0].id}
                            onTabSelect={(_event, selectedItem) =>
                                interactCanvasController.transitionToState({
                                    assistantId:
                                        conversationAssistants.find((assistant) => assistant.id === selectedItem.value)
                                            ?.id ?? null,
                                })
                            }
                            size="small"
                        >
                            {conversationAssistants
                                .slice()
                                .sort((a, b) => a.name.localeCompare(b.name))
                                .map((assistant) => (
                                    <Tab value={assistant.id} key={assistant.id}>
                                        {assistant.name}
                                    </Tab>
                                ))}
                        </TabList>
                        <Button
                            appearance="secondary"
                            icon={<BookInformation24Regular />}
                            onClick={() => interactCanvasController.transitionToState({ open: false })}
                        />
                    </div>
                    {selectedAssistant && (
                        <AssistantCanvas
                            hideCloseButton
                            assistant={selectedAssistant}
                            conversationId={conversation.id}
                        />
                    )}
                </>
            )}
        </>
    );
};
