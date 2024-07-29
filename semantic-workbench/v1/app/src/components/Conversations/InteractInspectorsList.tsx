// Copyright (c) Microsoft. All rights reserved.

import { Button, Tab, TabList, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { BookInformation24Regular } from '@fluentui/react-icons';
import React from 'react';
import { Assistant } from '../../models/Assistant';
import { Conversation } from '../../models/Conversation';
import { ConversationParticipant } from '../../models/ConversationParticipant';
import { useGetAssistantsQuery } from '../../services/workbench';
import { Loading } from '../App/Loading';
import { InteractInspectors } from './InteractInspectors';

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

interface InteractInspectorsListProps {
    conversation: Conversation;
    participants: ConversationParticipant[];
    onOpenChange: (value: boolean) => void;
}

export const InteractInspectorsList: React.FC<InteractInspectorsListProps> = (props) => {
    const { conversation, participants, onOpenChange } = props;
    const classes = useClasses();
    const { data: assistants, error: assistantsError, isLoading: isLoadingAssistants } = useGetAssistantsQuery();
    const [selectedAssistant, setSelectedAssistant] = React.useState<Assistant>();
    const [conversationAssistants, setConversationAssistants] = React.useState<Assistant[]>([]);

    if (assistantsError) {
        const errorMessage = JSON.stringify(assistantsError);
        throw new Error(`Error loading assistants: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (assistants && selectedAssistant === undefined) {
            const filteredAssistants = assistants.filter((assistant) =>
                participants.some((participant) => participant.active && participant.id === assistant.id),
            );
            setConversationAssistants(filteredAssistants);
            setSelectedAssistant(conversationAssistants[0]);
        }
    }, [assistants, participants, conversationAssistants, selectedAssistant]);

    if (isLoadingAssistants) {
        return <Loading />;
    }

    if (!assistants) {
        throw new Error('Assistants not found');
    }

    return (
        <>
            {conversationAssistants.length === 0 && (
                <div className={classes.noAssistants}>
                    No assistants found.
                    <Button
                        appearance="secondary"
                        onClick={() => onOpenChange(false)}
                        icon={<BookInformation24Regular />}
                    />
                </div>
            )}
            {conversationAssistants.length === 1 && (
                <InteractInspectors
                    assistant={conversationAssistants[0]}
                    conversationId={conversation.id}
                    onOpenChange={onOpenChange}
                />
            )}
            {conversationAssistants.length > 1 && (
                <>
                    <div className={classes.headerContent}>
                        <TabList
                            selectedValue={selectedAssistant?.id ?? conversationAssistants[0].id}
                            onTabSelect={(_event, selectedItem) => {
                                setSelectedAssistant(
                                    assistants.find((assistant) => assistant.id === selectedItem.value),
                                );
                            }}
                            size="small"
                        >
                            {conversationAssistants.map((assistant) => (
                                <Tab value={assistant.id} key={assistant.id}>
                                    {assistant.name}
                                </Tab>
                            ))}
                        </TabList>
                        <Button
                            appearance="secondary"
                            icon={<BookInformation24Regular />}
                            onClick={() => {
                                if (onOpenChange) onOpenChange(false);
                            }}
                        />
                    </div>
                    {selectedAssistant && (
                        <InteractInspectors assistant={selectedAssistant} conversationId={conversation.id} />
                    )}
                </>
            )}
        </>
    );
};
