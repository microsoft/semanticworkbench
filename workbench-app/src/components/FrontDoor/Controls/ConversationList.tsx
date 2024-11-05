// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';

import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useEnvironment } from '../../../libs/useEnvironment';
import { WorkbenchEventSource, WorkbenchEventSourceType } from '../../../libs/WorkbenchEventSource';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { useGetConversationsQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
import { PresenceMotionList } from '../../App/PresenceMotionList';
import { ConversationDuplicateDialog } from '../../Conversations/ConversationDuplicate';
import { ConversationRemoveDialog } from '../../Conversations/ConversationRemove';
import { ConversationRenameDialog } from '../../Conversations/ConversationRename';
import { ConversationShareDialog } from '../../Conversations/ConversationShare';
import { MemoizedConversationItem } from './ConversationItem';
import { ConversationListOptions } from './ConversationListOptions';

const useClasses = makeStyles({
    list: {
        gap: 0,
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    content: {
        ...shorthands.padding(0, tokens.spacingHorizontalM),
    },
});

export const ConversationList: React.FC = () => {
    const classes = useClasses();
    const environment = useEnvironment();
    const activeConversationId = useAppSelector((state) => state.app.activeConversationId);
    const localUserId = useAppSelector((state) => state.localUser.id);
    const { navigateToConversation } = useConversationUtility();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsLoading,
        isUninitialized: conversationsUninitialized,
        refetch: refetchConversations,
    } = useGetConversationsQuery();
    const [displayedConversations, setDisplayedConversations] = React.useState<Conversation[]>([]);

    const [renameConversation, setRenameConversation] = React.useState<Conversation>();
    const [duplicateConversation, setDuplicateConversation] = React.useState<Conversation>();
    const [shareConversation, setShareConversation] = React.useState<Conversation>();
    const [removeConversation, setRemoveConversation] = React.useState<Conversation>();
    const [selectedForActions, setSelectedForActions] = React.useState(new Set<string>());

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
            if (conversationsUninitialized) {
                // do not refetch conversations if it's the first time loading
                return;
            }

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
    }, [conversationsLoading, conversationsUninitialized, environment.url, refetchConversations]);

    const handleUpdateSelectedForActions = React.useCallback((conversationId: string, selected: boolean) => {
        if (selected) {
            setSelectedForActions((prev) => new Set(prev).add(conversationId));
        } else {
            setSelectedForActions((prev) => {
                const newSet = new Set(prev);
                newSet.delete(conversationId);
                return newSet;
            });
        }
    }, []);

    const handleItemSelect = React.useCallback(
        (conversation: Conversation) => {
            navigateToConversation(conversation.id);
        },
        [navigateToConversation],
    );

    const handleItemSelectForActions = React.useCallback(
        (conversation: Conversation, selected: boolean) => {
            handleUpdateSelectedForActions(conversation.id, selected);
        },
        [handleUpdateSelectedForActions],
    );

    const actionHelpers = React.useMemo(
        () => (
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
                {removeConversation && localUserId && (
                    <ConversationRemoveDialog
                        conversationId={removeConversation.id}
                        participantId={localUserId}
                        onRemove={() => {
                            if (activeConversationId === removeConversation.id) {
                                navigateToConversation(undefined);
                            }
                            setRemoveConversation(undefined);
                        }}
                        onCancel={() => setRemoveConversation(undefined)}
                    />
                )}
            </>
        ),
        [
            renameConversation,
            duplicateConversation,
            shareConversation,
            removeConversation,
            navigateToConversation,
            localUserId,
            activeConversationId,
        ],
    );

    if (conversationsLoading) {
        return <Loading />;
    }

    return (
        <>
            {actionHelpers}
            <ConversationListOptions
                conversations={conversations}
                selectedForActions={selectedForActions}
                onSelectedForActionsChanged={setSelectedForActions}
                onDisplayedConversationsChanged={setDisplayedConversations}
            />
            {!conversations || conversations.length === 0 ? (
                <div className={classes.content}>
                    <Text weight="semibold">No conversations found</Text>
                </div>
            ) : (
                <PresenceMotionList
                    className={classes.list}
                    items={displayedConversations.map((conversation) => (
                        // Use the individual memoized conversation item instead of the list
                        // to prevent re-rendering all items when one item changes
                        <MemoizedConversationItem
                            key={conversation.id}
                            conversation={conversation}
                            owned={conversation.ownerId === localUserId}
                            selected={activeConversationId === conversation.id}
                            selectedForActions={selectedForActions?.has(conversation.id)}
                            onSelect={handleItemSelect}
                            showSelectForActions={selectedForActions.size > 0}
                            onSelectForActions={handleItemSelectForActions}
                            onRename={setRenameConversation}
                            onDuplicate={setDuplicateConversation}
                            onShare={setShareConversation}
                            onRemove={setRemoveConversation}
                        />
                    ))}
                />
            )}
        </>
    );
};

export const MemoizedConversationList = React.memo(ConversationList);
