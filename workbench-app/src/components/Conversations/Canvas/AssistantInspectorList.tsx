// Copyright (c) Microsoft. All rights reserved.

import { Overflow, OverflowItem, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { AssistantStateDescription } from '../../../models/AssistantStateDescription';
import { useAppSelector } from '../../../redux/app/hooks';
import { OverflowMenu, OverflowMenuItemData } from '../../App/OverflowMenu';
import { AssistantInspector } from './AssistantInspector';

const useClasses = makeStyles({
    root: {
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
    },
    header: {
        flexShrink: 0,
        height: 'fit-content',
        overflow: 'hidden',
        ...shorthands.padding(tokens.spacingVerticalS),
        ...shorthands.borderBottom(tokens.strokeWidthThin, 'solid', tokens.colorNeutralStroke1),
    },
    body: {
        flexGrow: 1,
        overflowY: 'auto',
    },
});

interface AssistantInspectorListProps {
    conversationId: string;
    assistant: Assistant;
    stateDescriptions: AssistantStateDescription[];
}

export const AssistantInspectorList: React.FC<AssistantInspectorListProps> = (props) => {
    const { conversationId, assistant, stateDescriptions } = props;
    const classes = useClasses();
    const chatCanvasState = useAppSelector((state) => state.chatCanvas);
    const chatCanvasController = useChatCanvasController();

    const selectedStateDescription = React.useMemo(
        () =>
            stateDescriptions.find(
                (stateDescription) => stateDescription.id === chatCanvasState.selectedAssistantStateId,
            ) ?? stateDescriptions[0],
        [stateDescriptions, chatCanvasState.selectedAssistantStateId],
    );

    const tabItems = React.useMemo(
        () =>
            stateDescriptions
                .filter((stateDescription) => stateDescription.id !== 'config')
                .map(
                    (stateDescription): OverflowMenuItemData => ({
                        id: stateDescription.id,
                        name: stateDescription.displayName,
                    }),
                ),
        [stateDescriptions],
    );

    const handleTabSelect = React.useCallback(
        (id: string) => {
            chatCanvasController.transitionToState({ selectedAssistantStateId: id });
        },
        [chatCanvasController],
    );

    if (stateDescriptions.length === 1) {
        // Only one assistant state, no need to show tabs, just show the single assistant state
        return (
            <AssistantInspector
                assistantId={assistant.id}
                conversationId={conversationId}
                stateDescription={stateDescriptions[0]}
            />
        );
    }

    if (stateDescriptions.length === 0) {
        return (
            <div className={classes.root}>
                <div className={classes.header}>
                    <div>No assistant state inspectors available</div>
                </div>
            </div>
        );
    }

    return (
        <div className={classes.root}>
            <div className={classes.header}>
                <Overflow minimumVisible={1}>
                    <TabList
                        selectedValue={selectedStateDescription.id}
                        onTabSelect={(_, data) => handleTabSelect(data.value as string)}
                        size="small"
                    >
                        {tabItems.map((tabItem) => (
                            <OverflowItem
                                key={tabItem.id}
                                id={tabItem.id}
                                priority={tabItem.id === selectedStateDescription.id ? 2 : 1}
                            >
                                <Tab value={tabItem.id}>{tabItem.name}</Tab>
                            </OverflowItem>
                        ))}
                        <OverflowMenu items={tabItems} onItemSelect={handleTabSelect} />
                    </TabList>
                </Overflow>
            </div>
            <div className={classes.body}>
                <AssistantInspector
                    assistantId={assistant.id}
                    conversationId={conversationId}
                    stateDescription={selectedStateDescription}
                />
            </div>
        </div>
    );
};
