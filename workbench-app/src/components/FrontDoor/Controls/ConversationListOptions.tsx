// Copyright (c) Microsoft. All rights reserved.

import {
    Button,
    Input,
    Label,
    makeStyles,
    Menu,
    MenuButtonProps,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    Overflow,
    Select,
    shorthands,
    SplitButton,
    Text,
    tokens,
    Toolbar,
    Tooltip,
} from '@fluentui/react-components';
import {
    CheckboxCheckedFilled,
    CheckboxIndeterminateRegular,
    CheckboxUncheckedRegular,
    DismissRegular,
    FilterRegular,
    GlassesOffRegular,
    GlassesRegular,
    PinOffRegular,
    PinRegular,
    PlugDisconnectedRegular,
} from '@fluentui/react-icons';

import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { useAppSelector } from '../../../redux/app/hooks';
import { ConversationRemoveDialog } from '../../Conversations/ConversationRemove';

const useClasses = makeStyles({
    root: {
        position: 'sticky',
        top: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: tokens.spacingVerticalS,
        zIndex: tokens.zIndexPriority,
        backgroundColor: tokens.colorNeutralBackground2,
        ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalM),
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    displayOptions: {
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: tokens.spacingHorizontalS,
    },
    displayOption: {
        display: 'flex',
        flexDirection: 'row',
        gap: tokens.spacingHorizontalXS,
        alignItems: 'center',
    },
    bulkActions: {
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
    },
    bulkActionsLabel: {
        marginLeft: tokens.spacingHorizontalM,
        color: tokens.colorNeutralForeground2,
    },
    toolbarTextButton: {
        minWidth: 'auto',
        paddingLeft: tokens.spacingHorizontalXS,
        paddingRight: tokens.spacingHorizontalXS,
    },
});

interface ConversationListOptionsProps {
    conversations?: Conversation[];
    selectedForActions: Set<string>;
    onSelectedForActionsChanged: (selected: Set<string>) => void;
    onDisplayedConversationsChanged: (conversations: Conversation[]) => void;
}

export const ConversationListOptions: React.FC<ConversationListOptionsProps> = (props) => {
    const { conversations, selectedForActions, onSelectedForActionsChanged, onDisplayedConversationsChanged } = props;
    const classes = useClasses();
    const localUserId = useAppSelector((state) => state.localUser.id);
    const { hasUnreadMessages, markAllAsRead, markAllAsUnread, isPinned, setPinned } = useConversationUtility();
    const [filterString, setFilterString] = React.useState<string>('');
    const [displayFilter, setDisplayFilter] = React.useState<string>('');
    const [sortByName, setSortByName] = React.useState<boolean>(false);
    const [removeConversations, setRemoveConversations] = React.useState<Conversation[]>();
    const [displayedConversations, setDisplayedConversations] = React.useState<Conversation[]>(conversations || []);

    const sortByNameHelper = React.useCallback(
        (a: Conversation, b: Conversation) => a.title.localeCompare(b.title),
        [],
    );

    const sortByDateHelper = React.useCallback((a: Conversation, b: Conversation) => {
        const dateA = a.latest_message ? Utility.toDate(a.latest_message.timestamp) : Utility.toDate(a.created);
        const dateB = b.latest_message ? Utility.toDate(b.latest_message.timestamp) : Utility.toDate(b.created);
        return dateB.getTime() - dateA.getTime();
    }, []);

    // update displayed conversations when conversations or options change
    React.useEffect(() => {
        // filter conversations based on display filter and filter string
        const filteredConversations =
            conversations?.filter((conversation) => {
                switch (displayFilter) {
                    case 'Unread':
                        if (!hasUnreadMessages(conversation)) {
                            return false;
                        }
                        break;
                    case 'Pinned':
                        if (!isPinned(conversation)) {
                            return false;
                        }
                        break;
                    case 'Mine':
                        if (conversation.ownerId !== localUserId) {
                            return false;
                        }
                        break;
                    case 'Shared with me':
                        if (conversation.ownerId === localUserId) {
                            return false;
                        }
                        break;
                    default:
                        break;
                }

                return (
                    conversation.ownerId === localUserId &&
                    (!filterString ||
                        (filterString && conversation.title.toLowerCase().includes(filterString.toLowerCase())))
                );
            }) || [];

        // split conversations into pinned and unpinned
        const splitByPinned: Record<string, Conversation[]> = { pinned: [], unpinned: [] };
        filteredConversations.forEach((conversation) => {
            if (isPinned(conversation)) {
                splitByPinned.pinned.push(conversation);
            } else {
                splitByPinned.unpinned.push(conversation);
            }
        });

        const sortedConversations: Conversation[] = [];
        const sortHelperForSortType = sortByName ? sortByNameHelper : sortByDateHelper;

        // sort pinned conversations
        sortedConversations.push(...splitByPinned.pinned.sort(sortHelperForSortType));
        // sort unpinned conversations
        sortedConversations.push(...splitByPinned.unpinned.sort(sortHelperForSortType));

        setDisplayedConversations(sortedConversations);
        onDisplayedConversationsChanged(sortedConversations);
    }, [
        conversations,
        displayFilter,
        filterString,
        hasUnreadMessages,
        isPinned,
        onDisplayedConversationsChanged,
        sortByName,
        sortByNameHelper,
        sortByDateHelper,
        localUserId,
    ]);

    const bulkSelectForActionsIcon = React.useMemo(() => {
        const icons = {
            all: <CheckboxCheckedFilled color={tokens.colorCompoundBrandBackground} />,
            some: <CheckboxIndeterminateRegular color={tokens.colorCompoundBrandBackground} />,
            none: <CheckboxUncheckedRegular />,
        };

        if (selectedForActions.size === 0) {
            return icons.none;
        } else if (selectedForActions.size === displayedConversations.length) {
            return icons.all;
        } else {
            return icons.some;
        }
    }, [displayedConversations, selectedForActions]);

    const handleBulkSelectForActions = React.useCallback(
        (selectionType?: 'all' | 'none' | 'read' | 'unread' | 'pinned' | 'unpinned' | 'mine' | 'sharedWithMe') => {
            switch (selectionType) {
                case 'all':
                    onSelectedForActionsChanged(new Set(displayedConversations.map((conversation) => conversation.id)));
                    break;
                case 'none':
                    onSelectedForActionsChanged(new Set<string>());
                    break;
                case 'read':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => !hasUnreadMessages(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'unread':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => hasUnreadMessages(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'pinned':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => isPinned(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'unpinned':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => !isPinned(conversation))
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'mine':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => conversation.ownerId === localUserId)
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                case 'sharedWithMe':
                    onSelectedForActionsChanged(
                        new Set(
                            displayedConversations
                                .filter((conversation) => conversation.ownerId !== localUserId)
                                .map((conversation) => conversation.id),
                        ),
                    );
                    break;
                default:
                    // handle toggle all
                    if (selectedForActions.size > 0) {
                        // deselect all
                        onSelectedForActionsChanged(new Set<string>());
                    } else {
                        // select all
                        onSelectedForActionsChanged(
                            new Set(displayedConversations.map((conversation) => conversation.id)),
                        );
                    }
                    break;
            }
        },
        [
            localUserId,
            onSelectedForActionsChanged,
            displayedConversations,
            selectedForActions.size,
            hasUnreadMessages,
            isPinned,
        ],
    );

    const bulkSelectForActionsButton = React.useMemo(
        () => (
            <Menu positioning="below-end">
                <MenuTrigger disableButtonEnhancement>
                    {(triggerProps: MenuButtonProps) => (
                        <SplitButton
                            appearance="outline"
                            size="small"
                            menuButton={triggerProps}
                            primaryActionButton={{
                                onClick: () => handleBulkSelectForActions(),
                            }}
                            icon={bulkSelectForActionsIcon}
                        />
                    )}
                </MenuTrigger>
                <MenuPopover>
                    <MenuList>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('all')}
                            disabled={selectedForActions.size === displayedConversations.length}
                        >
                            All
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('none')}
                            disabled={selectedForActions.size === 0}
                        >
                            None
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('read')}
                            disabled={!displayedConversations.some((conversation) => !hasUnreadMessages(conversation))}
                        >
                            Read
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('unread')}
                            disabled={!displayedConversations.some(hasUnreadMessages)}
                        >
                            Unread
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('pinned')}
                            disabled={!displayedConversations.some(isPinned)}
                        >
                            Pinned
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('unpinned')}
                            disabled={!displayedConversations.some((conversation) => !isPinned(conversation))}
                        >
                            Unpinned
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('mine')}
                            disabled={
                                !displayedConversations.some((conversation) => conversation.ownerId === localUserId)
                            }
                        >
                            Mine
                        </MenuItem>
                        <MenuItem
                            onClick={() => handleBulkSelectForActions('sharedWithMe')}
                            disabled={
                                !displayedConversations.some((conversation) => conversation.ownerId !== localUserId)
                            }
                        >
                            Shared with me
                        </MenuItem>
                    </MenuList>
                </MenuPopover>
            </Menu>
        ),
        [
            localUserId,
            bulkSelectForActionsIcon,
            displayedConversations,
            handleBulkSelectForActions,
            hasUnreadMessages,
            isPinned,
            selectedForActions.size,
        ],
    );

    const enableBulkActions = React.useMemo(
        () =>
            selectedForActions.size > 0
                ? {
                      read: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && hasUnreadMessages(conversation),
                      ),
                      unread: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && !hasUnreadMessages(conversation),
                      ),
                      pin: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && !isPinned(conversation),
                      ),
                      unpin: conversations?.some(
                          (conversation) => selectedForActions.has(conversation.id) && isPinned(conversation),
                      ),
                      remove: true,
                  }
                : {
                      read: false,
                      unread: false,
                      pin: false,
                      unpin: false,
                      remove: false,
                  },
        [conversations, hasUnreadMessages, isPinned, selectedForActions],
    );

    const getSelectedConversations = React.useCallback(() => {
        return conversations?.filter((conversation) => selectedForActions.has(conversation.id)) ?? [];
    }, [conversations, selectedForActions]);

    const handleMarkAllAsReadForSelected = React.useCallback(async () => {
        await markAllAsRead(getSelectedConversations());
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, markAllAsRead, onSelectedForActionsChanged]);

    const handleMarkAsUnreadForSelected = React.useCallback(async () => {
        await markAllAsUnread(getSelectedConversations());
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, markAllAsUnread, onSelectedForActionsChanged]);

    const handleRemoveForSelected = React.useCallback(async () => {
        // set removeConversations to show remove dialog
        setRemoveConversations(getSelectedConversations());
        // don't clear selected conversations until after the user confirms the removal
    }, [getSelectedConversations]);

    const handlePinForSelected = React.useCallback(async () => {
        await setPinned(getSelectedConversations(), true);
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, setPinned, onSelectedForActionsChanged]);

    const handleUnpinForSelected = React.useCallback(async () => {
        await setPinned(getSelectedConversations(), false);
        onSelectedForActionsChanged(new Set<string>());
    }, [getSelectedConversations, setPinned, onSelectedForActionsChanged]);

    const handleRemoveConversations = React.useCallback(() => {
        // reset removeConversations and clear selected conversations
        setRemoveConversations(undefined);
        onSelectedForActionsChanged(new Set<string>());
    }, [onSelectedForActionsChanged]);

    const bulkSelectForActionsToolbar = React.useMemo(
        () => (
            <Overflow padding={90}>
                <Toolbar size="small">
                    <Tooltip content="Mark selected conversations as read" relationship="label">
                        <Button
                            className={classes.toolbarTextButton}
                            appearance="transparent"
                            icon={<GlassesRegular />}
                            disabled={!enableBulkActions.read}
                            onClick={handleMarkAllAsReadForSelected}
                        />
                    </Tooltip>
                    <Tooltip content="Mark selected conversations as unread" relationship="label">
                        <Button
                            appearance="transparent"
                            icon={<GlassesOffRegular />}
                            disabled={!enableBulkActions.unread}
                            onClick={handleMarkAsUnreadForSelected}
                        />
                    </Tooltip>
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
                    <Tooltip content="Remove selected conversations" relationship="label">
                        <Button
                            appearance="subtle"
                            icon={<PlugDisconnectedRegular />}
                            disabled={!enableBulkActions.remove}
                            onClick={handleRemoveForSelected}
                        />
                    </Tooltip>
                </Toolbar>
            </Overflow>
        ),
        [
            classes.toolbarTextButton,
            enableBulkActions.pin,
            enableBulkActions.read,
            enableBulkActions.remove,
            enableBulkActions.unpin,
            enableBulkActions.unread,
            handleMarkAllAsReadForSelected,
            handleMarkAsUnreadForSelected,
            handlePinForSelected,
            handleRemoveForSelected,
            handleUnpinForSelected,
        ],
    );

    return (
        <div className={classes.root}>
            {removeConversations && localUserId && (
                <ConversationRemoveDialog
                    conversations={removeConversations}
                    participantId={localUserId}
                    onRemove={handleRemoveConversations}
                    onCancel={() => setRemoveConversations(undefined)}
                />
            )}
            <div className={classes.header}>
                <Text weight="semibold">Conversations</Text>
            </div>
            <Input
                contentBefore={<FilterRegular />}
                contentAfter={
                    filterString && (
                        <Button
                            icon={<DismissRegular />}
                            appearance="transparent"
                            onClick={() => setFilterString('')}
                        />
                    )
                }
                placeholder="Filter"
                value={filterString}
                onChange={(_event, data) => setFilterString(data.value)}
            />
            <div className={classes.displayOptions}>
                <Select
                    size="small"
                    defaultValue={sortByName ? 'Sort by name' : 'Sort by date'}
                    onChange={(_event, data) => setSortByName(data.value === 'Sort by name')}
                >
                    <option>Sort by name</option>
                    <option>Sort by date</option>
                </Select>
                <div className={classes.displayOption}>
                    <Label size="small">Show</Label>
                    <Select size="small" defaultValue="All" onChange={(_event, data) => setDisplayFilter(data.value)}>
                        <option>All</option>
                        <option disabled={conversations?.every((conversation) => !hasUnreadMessages(conversation))}>
                            Unread
                        </option>
                        <option disabled={conversations?.every((conversation) => !isPinned(conversation))}>
                            Pinned
                        </option>
                        <option disabled={conversations?.every((conversation) => conversation.ownerId !== localUserId)}>
                            Mine
                        </option>
                        <option disabled={conversations?.every((conversation) => conversation.ownerId === localUserId)}>
                            Shared with me
                        </option>
                    </Select>
                </div>
            </div>
            <div className={classes.bulkActions}>
                {bulkSelectForActionsButton}
                <Label className={classes.bulkActionsLabel} size="small">
                    Actions
                </Label>
                {bulkSelectForActionsToolbar}
            </div>
        </div>
    );
};
