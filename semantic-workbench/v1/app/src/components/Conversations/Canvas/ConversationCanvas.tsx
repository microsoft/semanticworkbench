// Copyright (c) Microsoft. All rights reserved.

import { Button, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../../models/Assistant';
import { Conversation } from '../../../models/Conversation';
import { ConversationFile } from '../../../models/ConversationFile';
import { useAppDispatch, useAppSelector } from '../../../redux/app/hooks';
import { setInspector } from '../../../redux/features/app/appSlice';
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

interface ConversationCanvasProps {
    conversationAssistants: Assistant[];
    conversationFiles: ConversationFile[];
    conversation: Conversation;
}

export const ConversationCanvas: React.FC<ConversationCanvasProps> = (props) => {
    const { conversationAssistants, conversation } = props;
    const classes = useClasses();
    const { inspector } = useAppSelector((state) => state.app);
    const dispatch = useAppDispatch();

    React.useEffect(() => {
        if (conversationAssistants.length === 0) {
            if (inspector?.assistantId) {
                dispatch(setInspector({ assistantId: null }));
            }
            return;
        }

        // Verify the selected assistant is still in the list
        if (
            inspector?.assistantId &&
            conversationAssistants.some((assistant) => assistant.id === inspector.assistantId)
        ) {
            // Assistant is still in the list
            return;
        }

        // Select the first assistant in the list
        dispatch(setInspector({ assistantId: conversationAssistants[0].id }));
    }, [conversationAssistants, dispatch, inspector]);

    const selectedAssistant = conversationAssistants.find((assistant) => assistant.id === inspector?.assistantId);

    return (
        <>
            {conversationAssistants.length === 0 && (
                <div className={classes.noAssistants}>
                    No assistants found.
                    <Button
                        appearance="secondary"
                        onClick={() => dispatch(setInspector({ open: false }))}
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
                                dispatch(
                                    setInspector({
                                        assistantId:
                                            conversationAssistants.find(
                                                (assistant) => assistant.id === selectedItem.value,
                                            )?.id ?? null,
                                    }),
                                )
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
                            onClick={() => {
                                dispatch(setInspector({ open: false }));
                            }}
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
