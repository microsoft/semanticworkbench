// Copyright (c) Microsoft. All rights reserved.

import { Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { AssistantCanvas } from './AssistantCanvas';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    },
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
    selectedAssistant?: Assistant;
    conversationAssistants: Assistant[];
    conversation: Conversation;
}

export const AssistantCanvasList: React.FC<AssistantCanvasListProps> = (props) => {
    const { selectedAssistant, conversationAssistants, conversation } = props;
    const classes = useClasses();
    const chatCanvasController = useChatCanvasController();

    if (conversationAssistants.length === 1) {
        // Only one assistant, no need to show tabs, just show the single assistant
        return <AssistantCanvas assistant={conversationAssistants[0]} conversationId={conversation.id} />;
    }

    const assistant = selectedAssistant ?? conversationAssistants[0];

    // Multiple assistants, show tabs
    return (
        <div className={classes.root}>
            <div className={classes.headerContent}>
                <TabList
                    selectedValue={assistant.id}
                    onTabSelect={(_event, selectedItem) => {
                        // Find the assistant that corresponds to the selected tab
                        const conversationAssistant = conversationAssistants.find(
                            (conversationAssistant) => conversationAssistant.id === selectedItem.value,
                        );

                        // Set the new assistant as the active assistant
                        // If we can't find the assistant, we'll set the assistant to undefined
                        chatCanvasController.transitionToState({
                            selectedAssistantId: conversationAssistant?.id,
                            selectedAssistantStateId: undefined,
                        });
                    }}
                    size="small"
                >
                    {conversationAssistants.slice().map((assistant) => (
                        <Tab value={assistant.id} key={assistant.id}>
                            {assistant.name}
                        </Tab>
                    ))}
                </TabList>
            </div>
            <AssistantCanvas assistant={assistant} conversationId={conversation.id} />
        </div>
    );
};
