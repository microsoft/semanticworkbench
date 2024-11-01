// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';

import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useEnvironment } from '../../../libs/useEnvironment';
import { useLocalUserAccount } from '../../../libs/useLocalUserAccount';
import { WorkbenchEventSource, WorkbenchEventSourceType } from '../../../libs/WorkbenchEventSource';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { useGetConversationsQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
import { PresenceMotionList } from '../../App/PresenceMotionList';
import { ConversationDuplicateDialog } from '../../Conversations/ConversationDuplicate';
import { useConversationExport } from '../../Conversations/ConversationExport';
import { ConversationRemoveDialog } from '../../Conversations/ConversationRemove';
import { ConversationRenameDialog } from '../../Conversations/ConversationRename';
import { ConversationShareDialog } from '../../Conversations/ConversationShare';
import { ConversationItem } from './ConversationItem';
import { ConversationListOptions } from './ConversationListOptions';

const useClasses = makeStyles({
    list: {
        gap: 0,
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    noResults: {
        ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
});

export const ConversationList: React.FC = () => {
    const classes = useClasses();
    const { getUserId } = useLocalUserAccount();
    const environment = useEnvironment();
    const { activeConversationId } = useAppSelector((state) => state.app);
    const { navigateToConversation } = useConversationUtility();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsLoading,
        refetch: refetchConversations,
    } = useGetConversationsQuery();
    const [displayedConversations, setDisplayedConversations] = React.useState<Conversation[]>([]);

    const [renameConversation, setRenameConversation] = React.useState<Conversation>();
    const { exportConversation } = useConversationExport();
    const [duplicateConversation, setDuplicateConversation] = React.useState<Conversation>();
    const [shareConversation, setShareConversation] = React.useState<Conversation>();
    const [removeConversation, setRemoveConversation] = React.useState<Conversation>();
    const [selectedForActions, setSelectedForActions] = React.useState(new Set<string>());

    const userId = getUserId();

    if (conversationsError) {
        const errorMessage = JSON.stringify(conversationsError);
        throw new Error(`Error loading conversations: ${errorMessage}`);
    }

    React.useEffect(() => {
        if (conversationsLoading) {
            return;
        }

        // handle new message events
        const conversationHandler = async (_event: EventSourceMessage) => {
            // refetch conversations to update the latest message
            await refetchConversations();
        };

        (async () => {
            // create or update the event source
            const workbenchEventSource = await WorkbenchEventSource.createOrUpdate(
                environment.url,
                WorkbenchEventSourceType.User,
            );
            workbenchEventSource.addEventListener('message.created', conversationHandler);
            workbenchEventSource.addEventListener('message.deleted', conversationHandler);
            workbenchEventSource.addEventListener('conversation.updated', conversationHandler);
            workbenchEventSource.addEventListener('participant.created', conversationHandler);
            workbenchEventSource.addEventListener('participant.updated', conversationHandler);
        })();

        return () => {
            // remove event listeners
            (async () => {
                const workbenchEventSource = await WorkbenchEventSource.getInstance(WorkbenchEventSourceType.User);
                workbenchEventSource.removeEventListener('message.created', conversationHandler);
                workbenchEventSource.removeEventListener('message.deleted', conversationHandler);
                workbenchEventSource.removeEventListener('conversation.updated', conversationHandler);
                workbenchEventSource.removeEventListener('participant.created', conversationHandler);
                workbenchEventSource.removeEventListener('participant.updated', conversationHandler);
            })();
        };
    }, [conversationsLoading, environment.url, refetchConversations]);

    if (conversationsLoading) {
        return <Loading />;
    }

    const noConversations = (
        <Text className={classes.noResults} weight="semibold">
            No conversations found.
        </Text>
    );
    if (!conversations) {
        return noConversations;
    }

    const handleUpdateSelectedForActions = (conversationId: string, selected: boolean) => {
        if (selected) {
            setSelectedForActions((prev) => new Set(prev).add(conversationId));
        } else {
            setSelectedForActions((prev) => {
                const newSet = new Set(prev);
                newSet.delete(conversationId);
                return newSet;
            });
        }
    };

    return (
        <>
            {renameConversation && (
                <ConversationRenameDialog
                    id={renameConversation.id}
                    value={renameConversation.title}
                    onRename={async () => setRenameConversation(undefined)}
                    onCancel={() => setRenameConversation(undefined)}
                />
            )}
            {duplicateConversation && (
                <ConversationDuplicateDialog
                    id={duplicateConversation.id}
                    onDuplicate={(id) => navigateToConversation(id)}
                    onCancel={() => setDuplicateConversation(undefined)}
                />
            )}
            {shareConversation && (
                <ConversationShareDialog
                    conversation={shareConversation}
                    onClose={() => setShareConversation(undefined)}
                />
            )}
            {removeConversation && (
                <ConversationRemoveDialog
                    conversationId={removeConversation.id}
                    participantId={userId}
                    onRemove={() => {
                        if (activeConversationId === removeConversation.id) {
                            navigateToConversation(undefined);
                        }
                        setRemoveConversation(undefined);
                    }}
                    onCancel={() => setRemoveConversation(undefined)}
                />
            )}
            <ConversationListOptions
                conversations={conversations}
                selectedForActions={selectedForActions}
                onSelectedForActionsChanged={setSelectedForActions}
                onDisplayedConversationsChanged={setDisplayedConversations}
            />
            {displayedConversations.length === 0 && noConversations}
            <PresenceMotionList
                className={classes.list}
                items={displayedConversations.map((conversation) => (
                    <ConversationItem
                        key={conversation.id}
                        conversation={conversation}
                        owned={conversation.ownerId === userId}
                        selected={activeConversationId === conversation.id}
                        selectedForActions={selectedForActions?.has(conversation.id)}
                        onSelect={() => navigateToConversation(conversation.id)}
                        showSelectForActions={selectedForActions.size > 0}
                        onSelectForActions={(_, selected) => handleUpdateSelectedForActions(conversation.id, selected)}
                        onExport={() => exportConversation(conversation.id)}
                        onRename={setRenameConversation}
                        onDuplicate={setDuplicateConversation}
                        onShare={setShareConversation}
                        onRemove={setRemoveConversation}
                    />
                ))}
            />
        </>
    );
};
