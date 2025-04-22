// Copyright (c) Microsoft. All rights reserved.

import { Overflow, OverflowItem, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useChatCanvasController } from '../../../libs/useChatCanvasController';
import { Assistant } from '../../../models/Assistant';
import { ConversationStateDescription } from '../../../models/ConversationStateDescription';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchConversationEvents } from '../../../routes/FrontDoor';
import { useGetConversationStateQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
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
    stateDescriptions: ConversationStateDescription[];
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

    const {
        data: state,
        error: stateError,
        isLoading: isLoadingState,
        refetch: refetchState,
    } = useGetConversationStateQuery(
        { assistantId: assistant.id, stateId: selectedStateDescription.id, conversationId },
        { refetchOnMountOrArgChange: true },
    );

    if (stateError) {
        const errorMessage = JSON.stringify(stateError);
        throw new Error(`Error loading assistant state: ${errorMessage}`);
    }

    const handleEvent = React.useCallback(
        (event: EventSourceMessage) => {
            const { data } = JSON.parse(event.data);
            if (assistant.id !== data['assistant_id']) return;
            if (selectedStateDescription.id !== data['state_id']) return;
            if (conversationId !== data['conversation_id']) return;
            refetchState();
        },
        [assistant.id, selectedStateDescription.id, conversationId, refetchState],
    );

    React.useEffect(() => {
        workbenchConversationEvents.addEventListener('assistant.state.updated', handleEvent);

        return () => {
            workbenchConversationEvents.removeEventListener('assistant.state.updated', handleEvent);
        };
    }, [handleEvent]);

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

    const component = React.useMemo(() => {
        if (!state || isLoadingState) {
            return <Loading />;
        }
        if (stateDescriptions.length === 1) {
            // Only one assistant state, no need to show tabs, just show the single assistant state
            return (
                <AssistantInspector
                    assistantId={assistant.id}
                    conversationId={conversationId}
                    stateDescription={stateDescriptions[0]}
                    state={state}
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
                        state={state}
                    />
                </div>
            </div>
        );
    }, [
        state,
        isLoadingState,
        stateDescriptions,
        classes.root,
        classes.header,
        classes.body,
        selectedStateDescription,
        tabItems,
        handleTabSelect,
        assistant.id,
        conversationId,
    ]);
    return <>{component}</>;
};
