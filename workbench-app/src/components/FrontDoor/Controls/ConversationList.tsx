// Copyright (c) Microsoft. All rights reserved.

import { Button, Input, Select, Text, makeStyles, shorthands, tokens } from '@fluentui/react-components';
import { DismissRegular, FilterRegular } from '@fluentui/react-icons';

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
});

export const ConversationList: React.FC = () => {
    const classes = useClasses();
    const { getUserId } = useLocalUserAccount();
    const environment = useEnvironment();
    const { activeConversationId } = useAppSelector((state) => state.app);
    const { navigateToConversation, isPinned } = useConversationUtility();
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
                onSelect={() => navigateToConversation(conversation.id)}
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
            </div>
            {myConversations.length === 0 && <Text>No Conversations found.</Text>}
            <PresenceMotionList className={classes.list} items={conversationsToItems(myConversations)} />
            {conversationsSharedWithMe.length > 0 && <Text>Shared with me</Text>}
            <PresenceMotionList className={classes.list} items={conversationsToItems(conversationsSharedWithMe)} />
        </>
    );
};
