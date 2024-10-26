// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Input,
    Menu,
    MenuButtonProps,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Select,
    SplitButton,
    Text,
    Tooltip,
    makeStyles,
    mergeClasses,
    tokens,
} from '@fluentui/react-components';
import {
    ArrowDownloadRegular,
    DismissRegular,
    EditRegular,
    FilterRegular,
    PlugDisconnectedRegular,
    SaveCopyRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { useConversationUtility } from '../../libs/useConversationUtility';
import { useLocalUserAccount } from '../../libs/useLocalUserAccount';
import { Conversation } from '../../models/Conversation';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetConversationsQuery } from '../../services/workbench';
import { Loading } from '../App/Loading';
import { PresenceMotionList } from '../App/PresenceMotionList';
import { ConversationDuplicateDialog } from '../Conversations/ConversationDuplicate';
import { useConversationExport } from '../Conversations/ConversationExport';
import { ConversationRemoveDialog } from '../Conversations/ConversationRemove';
import { ConversationRenameDialog } from '../Conversations/ConversationRename';
import { ConversationShareDialog } from '../Conversations/ConversationShare';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const useClasses = makeStyles({
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
    const { activeConversationId } = useAppSelector((state) => state.app);
    const { navigateToConversation } = useConversationUtility();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsLoading,
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

    const createdStringToDate = (created: string) => {
        return dayjs.utc(created).tz(dayjs.tz.guess()).toDate();
    };

    const conversationsToItems = (conversations: Conversation[]) => {
        return conversations
            ?.filter((conversation) => conversation.metadata?.workflow_run_id === undefined)
            .toSorted((a, b) =>
                sortByName
                    ? // Sort by title, ascending
                      a.title.toLocaleLowerCase().localeCompare(b.title.toLocaleLowerCase())
                    : // Sort by created date, descending
                      createdStringToDate(b.created).getTime() - createdStringToDate(a.created).getTime(),
            )
            .map((conversation) => (
                <Menu key={conversation.id} positioning="below-end">
                    <MenuTrigger disableButtonEnhancement>
                        {(triggerProps: MenuButtonProps) => (
                            <SplitButton
                                appearance="subtle"
                                menuButton={triggerProps}
                                primaryActionButton={{
                                    className: mergeClasses(
                                        classes.conversationButton,
                                        activeConversationId === conversation.id ? classes.active : '',
                                    ),
                                    onClick: () => navigateToConversation(conversation.id),
                                }}
                            >
                                {conversation.title}
                            </SplitButton>
                        )}
                    </MenuTrigger>
                    <MenuPopover>
                        <MenuList>
                            <MenuItem
                                icon={<EditRegular />}
                                onClick={() => setRenameConversation(conversation)}
                                disabled={conversation.ownerId !== userId}
                            >
                                Rename
                            </MenuItem>
                            <MenuItem
                                icon={<ArrowDownloadRegular />}
                                onClick={() => exportConversation(conversation.id)}
                            >
                                Export
                            </MenuItem>
                            <MenuItem icon={<SaveCopyRegular />} onClick={() => setDuplicateConversation(conversation)}>
                                Duplicate
                            </MenuItem>
                            <MenuItem icon={<ShareRegular />} onClick={() => setShareConversation(conversation)}>
                                Share
                            </MenuItem>
                            <MenuItem
                                icon={<PlugDisconnectedRegular />}
                                onClick={() => setRemoveConversation(conversation)}
                                disabled={conversation.id === activeConversationId}
                            >
                                {conversation.id === activeConversationId ? (
                                    <Tooltip content="Cannot remove currently active conversation" relationship="label">
                                        <Text>Remove</Text>
                                    </Tooltip>
                                ) : (
                                    'Remove'
                                )}
                            </MenuItem>
                        </MenuList>
                    </MenuPopover>
                </Menu>
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
            {myConversations.length === 0 && <Text>No Conversations found.</Text>}
            <PresenceMotionList items={conversationsToItems(myConversations)} />
            {conversationsSharedWithMe.length > 0 && <Text>Shared with me</Text>}
            <PresenceMotionList items={conversationsToItems(conversationsSharedWithMe)} />
        </>
    );
};
