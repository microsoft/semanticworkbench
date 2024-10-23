// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Input,
    Menu,
    MenuButtonProps,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Select,
    SplitButton,
    Text,
    makeStyles,
    mergeClasses,
    tokens,
} from '@fluentui/react-components';
import { DismissRegular, FilterRegular } from '@fluentui/react-icons';
import dayjs from 'dayjs';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useLocalUserAccount } from '../../libs/useLocalUserAccount';
import { Conversation } from '../../models/Conversation';
import { useAppSelector } from '../../redux/app/hooks';
import { useGetConversationsQuery, useUpdateConversationMutation } from '../../services/workbench';
import { Loading } from '../App/Loading';
import { PresenceMotionList } from '../App/PresenceMotionList';
import { ConversationDuplicate } from '../Conversations/ConversationDuplicate';
import { ConversationExport } from '../Conversations/ConversationExport';
import { ConversationRemove } from '../Conversations/ConversationRemove';
import { ConversationRename } from '../Conversations/ConversationRename';
import { ConversationShare } from '../Conversations/ConversationShare';

dayjs.extend(utc);
dayjs.extend(timezone);
dayjs.tz.guess();

const redirectPath = '/frontdoor/';

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
    const navigate = useNavigate();
    const {
        data: conversations,
        error: conversationsError,
        isLoading: conversationsLoading,
    } = useGetConversationsQuery();
    const [updateConversation] = useUpdateConversationMutation();
    const [filter, setFilter] = React.useState<string>('');
    const [sortByName, setSortByName] = React.useState<boolean>(false);

    if (conversationsError) {
        const errorMessage = JSON.stringify(conversationsError);
        throw new Error(`Error loading conversations: ${errorMessage}`);
    }

    const handleConversationRename = React.useCallback(
        async (id: string, newTitle: string) => {
            await updateConversation({ id, title: newTitle });
        },
        [updateConversation],
    );

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
                                    onClick: () => navigate([redirectPath, conversation.id].join('')),
                                }}
                            >
                                {conversation.title}
                            </SplitButton>
                        )}
                    </MenuTrigger>
                    <MenuPopover>
                        <MenuList>
                            <ConversationRename
                                disabled={conversation.ownerId !== userId}
                                id={conversation.id}
                                value={conversation.title}
                                onRename={handleConversationRename}
                                asMenuItem
                            />
                            <ConversationExport conversationId={conversation.id} asMenuItem />
                            <ConversationDuplicate conversation={conversation} asMenuItem />
                            <ConversationShare conversation={conversation} asMenuItem />
                            <ConversationRemove conversation={conversation} participantId={userId} asMenuItem />
                        </MenuList>
                    </MenuPopover>
                </Menu>
            ));
    };

    return (
        <>
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
