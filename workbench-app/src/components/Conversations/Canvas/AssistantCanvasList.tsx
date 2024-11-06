// Copyright (c) Microsoft. All rights reserved.

import { Overflow, OverflowItem, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { OverflowMenu, OverflowMenuItemData } from '../../App/OverflowMenu';
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
    header: {
        overflow: 'hidden',
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
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

    const tabItems = React.useMemo(
        () =>
            conversationAssistants.slice().map(
                (assistant): OverflowMenuItemData => ({
                    id: assistant.id,
                    name: assistant.name,
                }),
            ),
        [conversationAssistants],
    );

    const handleTabSelect = React.useCallback(
        (id: string) => {
            // Find the assistant that corresponds to the selected tab
            const conversationAssistant = conversationAssistants.find(
                (conversationAssistant) => conversationAssistant.id === id,
            );

            // Set the new assistant as the active assistant
            // If we can't find the assistant, we'll set the assistant to undefined
            chatCanvasController.transitionToState({
                selectedAssistantId: conversationAssistant?.id,
                selectedAssistantStateId: undefined,
            });
        },
        [chatCanvasController, conversationAssistants],
    );

    const assistant = React.useMemo(
        () => selectedAssistant ?? conversationAssistants[0],
        [selectedAssistant, conversationAssistants],
    );

    if (conversationAssistants.length === 1) {
        // Only one assistant, no need to show tabs, just show the single assistant
        return <AssistantCanvas assistant={conversationAssistants[0]} conversationId={conversation.id} />;
    }

    // Multiple assistants, show tabs
    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Overflow minimumVisible={1}>
                    <TabList
                        selectedValue={assistant.id}
                        onTabSelect={(_, data) => handleTabSelect(data.value as string)}
                        size="small"
                    >
                        {tabItems.map((tabItem) => (
                            <OverflowItem
                                key={tabItem.id}
                                id={tabItem.id}
                                priority={tabItem.id === assistant.id ? 2 : 1}
                            >
                                <Tab value={tabItem.id}>{tabItem.name}</Tab>
                            </OverflowItem>
                        ))}
                        <OverflowMenu items={tabItems} onItemSelect={handleTabSelect} />
                    </TabList>
                </Overflow>
            </div>
            <AssistantCanvas assistant={assistant} conversationId={conversation.id} />
        </div>
    );
};
