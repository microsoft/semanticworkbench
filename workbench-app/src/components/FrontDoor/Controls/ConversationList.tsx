// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Checkbox,
    Input,
    Link,
    Select,
    Text,
    Tooltip,
    makeStyles,
    shorthands,
    tokens,
} from '@fluentui/react-components';
import {
    DismissRegular,
    FilterRegular,
    PinOffRegular,
    PinRegular,
    PlugDisconnectedRegular,
} from '@fluentui/react-icons';

import { EventSourceMessage } from '@microsoft/fetch-event-source';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { useEnvironment } from '../../../libs/useEnvironment';
import { useLocalUserAccount } from '../../../libs/useLocalUserAccount';
import { Utility } from '../../../libs/Utility';
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

const useClasses = makeStyles({
    actions: {
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        zIndex: tokens.zIndexPriority,
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    list: {
        gap: 0,
        ...shorthands.padding(0, tokens.spacingHorizontalM, tokens.spacingVerticalM, tokens.spacingHorizontalM),
    },
    conversationButton: {
        width: '250px',
        justifyContent: 'start',
        textAlign: 'start',
    },
    active: {
        backgroundColor: tokens.colorBrandBackgroundInvertedSelected,
    },
    bulkActions: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
});

export const ConversationList: React.FC = () => {
    const classes = useClasses();
    const { getUserId } = useLocalUserAccount();
    const environment = useEnvironment();
    const { activeConversationId } = useAppSelector((state) => state.app);
    const { navigateToConversation, hasUnreadMessages, markAllAsRead, markAsUnread, isPinned, setPinned } =
        useConversationUtility();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsLoading,
        refetch: refetchConversations,
    } = useGetConversationsQuery();
    const [filter, setFilter] = React.useState<string>('');
    const [sortByName, setSortByName] = React.useState<boolean>(false);

    const [renameConversation, setRenameConversation] = React.useState<Conversation>();
    const { exportConversation } = useConversationExport();
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

    const userId = getUserId();
    const myConversations =
        conversations?.filter(
            (conversation) =>
                conversation.ownerId === userId &&
                (!filter || (filter && conversation.title.toLowerCase().includes(filter.toLowerCase()))),
        ) || [];
    const conversationsSharedWithMe =
        conversations?.filter(
            (conversation) =>
                conversation.ownerId !== userId &&
                (!filter || (filter && conversation.title.toLowerCase().includes(filter.toLowerCase()))),
        ) || [];

    const sortByNameHelper = (a: Conversation, b: Conversation) => a.title.localeCompare(b.title);

    const sortByDateHelper = (a: Conversation, b: Conversation) => {
        const dateA = a.latest_message ? Utility.toDate(a.latest_message.timestamp) : Utility.toDate(a.created);
        const dateB = b.latest_message ? Utility.toDate(b.latest_message.timestamp) : Utility.toDate(b.created);
        return dateB.getTime() - dateA.getTime();
    };

    const handleSelectedForActions = (conversationId: string, selected: boolean) => {
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

    const getSelectedConversations = () => {
        return conversations?.filter((conversation) => selectedForActions.has(conversation.id)) ?? [];
    };

    const handleMarkAllAsReadForSelected = async () => {
        await markAllAsRead(getSelectedConversations());
        setSelectedForActions(new Set<string>());
    };

    const handleMarkAsUnreadForSelected = async () => {
        await markAsUnread(getSelectedConversations());
        setSelectedForActions(new Set<string>());
    };

    const handleRemoveForSelected = async () => {
        // TODO: implement remove conversation
        setSelectedForActions(new Set<string>());
    };

    const handlePinForSelected = async () => {
        await setPinned(getSelectedConversations(), true);
        setSelectedForActions(new Set<string>());
    };

    const handleUnpinForSelected = async () => {
        await setPinned(getSelectedConversations(), false);
        setSelectedForActions(new Set<string>());
    };

    const enableBulkActions =
        selectedForActions.size > 0
            ? {
                  read: conversations?.some(
                      (conversation) => selectedForActions.has(conversation.id) && hasUnreadMessages(conversation),
                  ),
                  unread: conversations?.some(
                      (conversation) => selectedForActions.has(conversation.id) && !hasUnreadMessages(conversation),
                  ),
                  remove: true,
                  pin: conversations?.some(
                      (conversation) => selectedForActions.has(conversation.id) && !isPinned(conversation),
                  ),
                  unpin: conversations?.some(
                      (conversation) => selectedForActions.has(conversation.id) && isPinned(conversation),
                  ),
              }
            : {
                  read: false,
                  unread: false,
                  remove: false,
                  pin: false,
                  unpin: false,
              };

    const conversationsToItems = (conversationList: Conversation[]) => {
        const splitByPinned: Record<string, Conversation[]> = { pinned: [], unpinned: [] };
        conversationList.forEach((conversation) => {
            if (conversation.metadata?.workflow_run_id !== undefined) {
                return;
            }
            if (isPinned(conversation)) {
                splitByPinned.pinned.push(conversation);
            } else {
                splitByPinned.unpinned.push(conversation);
            }
        });

        const sortedConversationList: Conversation[] = [];
        const sortHelperForSortType = sortByName ? sortByNameHelper : sortByDateHelper;

        // sort pinned conversations
        sortedConversationList.push(...splitByPinned.pinned.sort(sortHelperForSortType));
        // sort unpinned conversations
        sortedConversationList.push(...splitByPinned.unpinned.sort(sortHelperForSortType));

        return sortedConversationList.map((conversation) => (
            <ConversationItem
                key={conversation.id}
                conversation={conversation}
                owned={conversation.ownerId === userId}
                selected={activeConversationId === conversation.id}
                selectedForActions={selectedForActions?.has(conversation.id)}
                onSelect={() => navigateToConversation(conversation.id)}
                showSelectForActions={selectedForActions.size > 0}
                onSelectForActions={(_, selected) => handleSelectedForActions(conversation.id, selected)}
                onExport={() => exportConversation(conversation.id)}
                onRename={setRenameConversation}
                onDuplicate={setDuplicateConversation}
                onShare={setShareConversation}
                onRemove={setRemoveConversation}
            />
        ));
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
            <div className={classes.actions}>
                <Text weight="semibold">Conversations</Text>
                <Input
                    contentBefore={<FilterRegular />}
                    contentAfter={
                        filter && (
                            <Button icon={<DismissRegular />} appearance="transparent" onClick={() => setFilter('')} />
                        )
                    }
                    placeholder="Filter"
                    value={filter}
                    onChange={(_event, data) => setFilter(data.value)}
                />
                <Select
                    defaultValue={sortByName ? 'Sort by name' : 'Sort by date'}
                    onChange={(_event, data) => setSortByName(data.value === 'Sort by name')}
                >
                    <option>Sort by name</option>
                    <option>Sort by date</option>
                </Select>
                <div className={classes.bulkActions}>
                    <Checkbox
                        checked={selectedForActions.size > 0}
                        onChange={(_event, data) => {
                            setSelectedForActions(
                                data.checked
                                    ? new Set(myConversations.map((conversation) => conversation.id))
                                    : new Set<string>(),
                            );
                        }}
                    />
                    <Link disabled={!enableBulkActions.read} onClick={handleMarkAllAsReadForSelected}>
                        Read
                    </Link>
                    &nbsp;|&nbsp;
                    <Link disabled={!enableBulkActions.unread} onClick={handleMarkAsUnreadForSelected}>
                        Unread
                    </Link>
                    &nbsp;|&nbsp;
                    <Tooltip content="Remove selected conversations" relationship="label">
                        <Button
                            // hide this until implemented
                            style={{ display: 'none' }}
                            appearance="subtle"
                            icon={<PlugDisconnectedRegular />}
                            disabled={!enableBulkActions.remove}
                            onClick={handleRemoveForSelected}
                        />
                    </Tooltip>
                    <Tooltip content="Pin selected conversations" relationship="label">
                        <Button
                            appearance="subtle"
                            icon={<PinRegular />}
                            disabled={!enableBulkActions.pin}
                            onClick={handlePinForSelected}
                        />
                    </Tooltip>
                    <Tooltip content="Unpin selected conversations" relationship="label">
                        <Button
                            appearance="subtle"
                            icon={<PinOffRegular />}
                            disabled={!enableBulkActions.unpin}
                            onClick={handleUnpinForSelected}
                        />
                    </Tooltip>
                </div>
            </div>
            {myConversations.length === 0 && <Text>No Conversations found.</Text>}
            <PresenceMotionList className={classes.list} items={conversationsToItems(myConversations)} />
            {conversationsSharedWithMe.length > 0 && <Text>Shared with me</Text>}
            <PresenceMotionList className={classes.list} items={conversationsToItems(conversationsSharedWithMe)} />
        </>
    );
};
