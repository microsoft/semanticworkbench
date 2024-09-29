// Copyright (c) Microsoft. All rights reserved.

import { Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useInteractCanvasController } from '../../../libs/useInteractCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
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

interface AssistantCanvasListProps {
    selectedAssistant: Assistant;
    conversationAssistants: Assistant[];
    conversation: Conversation;
}

export const AssistantCanvasList: React.FC<AssistantCanvasListProps> = (props) => {
    const { selectedAssistant, conversationAssistants, conversation } = props;
    const classes = useClasses();
    const interactCanvasController = useInteractCanvasController();

    if (!selectedAssistant) {
        return null;
    }

    if (conversationAssistants.length === 1) {
        // Only one assistant, no need to show tabs
        return <AssistantCanvas assistant={selectedAssistant} conversationId={conversation.id} />;
    }

    // Multiple assistants, show tabs
    return (
        <>
            <div className={classes.headerContent}>
                <TabList
                    selectedValue={selectedAssistant?.id ?? conversationAssistants[0].id}
                    onTabSelect={(_event, selectedItem) => {
                        // Find the assistant that corresponds to the selected tab
                        const assistant = conversationAssistants.find(
                            (assistant) => assistant.id === selectedItem.value,
                        );

                        // Set the new assistant as the active assistant
                        // If we can't find the assistant, we'll set the assistant to null
                        interactCanvasController.transitionToState({
                            assistantId: assistant?.id ?? null,
                        });
                    }}
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
            </div>
            {selectedAssistant && <AssistantCanvas assistant={selectedAssistant} conversationId={conversation.id} />}
        </>
    );
};
