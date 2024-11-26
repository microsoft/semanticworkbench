// Copyright (c) Microsoft. All rights reserved.

import { makeStyles, shorthands, Text, tokens } from '@fluentui/react-components';

import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useEnvironment } from '../../../libs/useEnvironment';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { workbenchUserEvents } from '../../../routes/FrontDoor';
import { useGetConversationsQuery } from '../../../services/workbench';
import { Loading } from '../../App/Loading';
import { PresenceMotionList } from '../../App/PresenceMotionList';
import { ConversationDuplicateDialog } from '../../Conversations/ConversationDuplicate';
import { ConversationExportWithStatusDialog } from '../../Conversations/ConversationExport';
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

interface ConversationListProps {
    parentConversationId?: string;
    hideChildConversations?: boolean;
}

export const ConversationList: React.FC<ConversationListProps> = (props) => {
    const { parentConversationId, hideChildConversations } = props;
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
    const [filteredConversations, setFilteredConversations] = React.useState<Conversation[]>();
    const [displayedConversations, setDisplayedConversations] = React.useState<Conversation[]>([]);

    const [renameConversation, setRenameConversation] = React.useState<Conversation>();
    const [duplicateConversation, setDuplicateConversation] = React.useState<Conversation>();
    const [exportConversation, setExportConversation] = React.useState<Conversation>();
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

        workbenchUserEvents.addEventListener('message.created', conversationHandler);
        workbenchUserEvents.addEventListener('message.deleted', conversationHandler);
        workbenchUserEvents.addEventListener('conversation.updated', conversationHandler);
        workbenchUserEvents.addEventListener('participant.created', conversationHandler);
        workbenchUserEvents.addEventListener('participant.updated', conversationHandler);

        return () => {
            // remove event listeners
            workbenchUserEvents.removeEventListener('message.created', conversationHandler);
            workbenchUserEvents.removeEventListener('message.deleted', conversationHandler);
            workbenchUserEvents.removeEventListener('conversation.updated', conversationHandler);
            workbenchUserEvents.removeEventListener('participant.created', conversationHandler);
            workbenchUserEvents.removeEventListener('participant.updated', conversationHandler);
        };
    }, [conversationsLoading, conversationsUninitialized, environment.url, refetchConversations]);

    React.useEffect(() => {
        if (conversationsLoading) {
            return;
        }

        setFilteredConversations(
            conversations?.filter((conversation) => {
                if (parentConversationId) {
                    if (hideChildConversations) {
                        return (
                            conversation.metadata?.['parent_conversation_id'] === undefined ||
                            conversation.metadata?.['parent_conversation_id'] !== parentConversationId
                        );
                    }
                    return conversation.metadata?.['parent_conversation_id'] === parentConversationId;
                }
                if (hideChildConversations) {
                    return conversation.metadata?.['parent_conversation_id'] === undefined;
                }
                return true;
            }),
        );
    }, [conversations, conversationsLoading, hideChildConversations, parentConversationId]);

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

    const handleDuplicateConversationComplete = React.useCallback(
        async (id: string) => {
            navigateToConversation(id);
            setDuplicateConversation(undefined);
        },
        [navigateToConversation],
    );

    const actionHelpers = React.useMemo(
        () => (
            <>
                <ConversationRenameDialog
                    conversationId={renameConversation?.id ?? ''}
                    value={renameConversation?.title ?? ''}
                    open={renameConversation !== undefined}
                    onOpenChange={() => setRenameConversation(undefined)}
                    onRename={async () => setRenameConversation(undefined)}
                />
                <ConversationDuplicateDialog
                    conversationId={duplicateConversation?.id ?? ''}
                    open={duplicateConversation !== undefined}
                    onOpenChange={() => setDuplicateConversation(undefined)}
                    onDuplicate={handleDuplicateConversationComplete}
                />
                <ConversationExportWithStatusDialog
                    conversationId={exportConversation?.id}
                    onExport={async () => setExportConversation(undefined)}
                />
                {shareConversation && (
                    <ConversationShareDialog
                        conversation={shareConversation}
                        onClose={() => setShareConversation(undefined)}
                    />
                )}
                {removeConversation && localUserId && (
                    <ConversationRemoveDialog
                        conversations={removeConversation}
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
            handleDuplicateConversationComplete,
            exportConversation,
            shareConversation,
            removeConversation,
            localUserId,
            activeConversationId,
            navigateToConversation,
        ],
    );

    if (conversationsLoading) {
        return <Loading />;
    }

    return (
        <>
            {actionHelpers}
            <ConversationListOptions
                conversations={filteredConversations}
                selectedForActions={selectedForActions}
                onSelectedForActionsChanged={setSelectedForActions}
                onDisplayedConversationsChanged={setDisplayedConversations}
            />
            {!filteredConversations || filteredConversations.length === 0 ? (
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
                            onExport={setExportConversation}
                            onShare={setShareConversation}
                            onRemove={setRemoveConversation}
                        />
                    ))}
                />
            )}
        </>
    );
};
