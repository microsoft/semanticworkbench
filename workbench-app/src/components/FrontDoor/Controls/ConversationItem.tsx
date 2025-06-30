import {
    Button,
    Caption1,
    Card,
    CardHeader,
    Checkbox,
    makeStyles,
    Menu,
    MenuItem,
    MenuList,
    MenuPopover,
    MenuTrigger,
    mergeClasses,
    Text,
    tokens,
    Tooltip,
} from '@fluentui/react-components';
import {
    ArrowDownloadRegular,
    EditRegular,
    GlassesOffRegular,
    GlassesRegular,
    MoreHorizontalRegular,
    Pin12Regular,
    PinOffRegular,
    PinRegular,
    PlugDisconnectedRegular,
    SaveCopyRegular,
    ShareRegular,
} from '@fluentui/react-icons';
import React from 'react';
import { useConversationUtility } from '../../../libs/useConversationUtility';
import { Utility } from '../../../libs/Utility';
import { Conversation } from '../../../models/Conversation';
import { ConversationParticipant } from '../../../models/ConversationParticipant';
import { useAppSelector } from '../../../redux/app/hooks';
import { MemoizedParticipantAvatarGroup } from '../../Conversations/ParticipantAvatarGroup';

const useClasses = makeStyles({
    cardHeader: {
        overflow: 'hidden',

        // Required to prevent overflow of the header and description
        // to support ellipsis and text overflow handling
        '& .fui-CardHeader__header': {
            overflow: 'hidden',
        },

        '& .fui-CardHeader__description': {
            overflow: 'hidden',
        },
    },
    header: {
        display: 'flex',
        flexDirection: 'row',
        flex: 1,
        gap: tokens.spacingHorizontalXS,
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
    },
    action: {
        flex: '0 0 auto',
        display: 'flex',
        flexDirection: 'column',
    },
    pin: {
        flex: '0 0 auto',
    },
    title: {
        flexGrow: 1,
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        minWidth: 0,
    },
    date: {
        marginLeft: tokens.spacingHorizontalXS,
        flexShrink: 0,
    },
    unread: {
        color: tokens.colorStrokeFocus2,
        fontWeight: '600',
    },
    description: {
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        width: '100%',
    },
    showingActions: {
        '& .fui-CardHeader__header': {
            width: 'calc(100% - 40px)',
        },

        '& .fui-CardHeader__description': {
            width: 'calc(100% - 40px)',
        },
    },
    selectCheckbox: {
        height: '24px',
    },
    moreButton: {
        paddingTop: 0,
        paddingBottom: 0,
    },
});

interface ConversationItemProps {
    conversation: Conversation;
    owned?: boolean;
    selected?: boolean;
    showSelectForActions?: boolean;
    selectedForActions?: boolean;
    onSelect?: (conversation: Conversation) => void;
    onExport?: (conversation: Conversation) => void;
    onRename?: (conversation: Conversation) => void;
    onDuplicate?: (conversation: Conversation) => void;
    onShare?: (conversation: Conversation) => void;
    onRemove?: (conversation: Conversation) => void;
    onSelectForActions?: (conversation: Conversation, selected: boolean) => void;
}

export const ConversationItem: React.FC<ConversationItemProps> = (props) => {
    const {
        conversation,
        owned,
        selected,
        onSelect,
        onExport,
        onRename,
        onDuplicate,
        onShare,
        onRemove,
        showSelectForActions,
        selectedForActions,
        onSelectForActions,
    } = props;
    const classes = useClasses();
    const {
        getOwnerParticipant,
        wasSharedWithMe,
        hasUnreadMessages,
        isPinned,
        setPinned,
        markAllAsRead,
        markAllAsUnread,
    } = useConversationUtility();
    const localUserId = useAppSelector((state) => state.localUser.id);
    const [isHovered, setIsHovered] = React.useState(false);

    const showActions = isHovered || showSelectForActions;

    const handleMenuItemClick = React.useCallback(
        (event: React.MouseEvent<HTMLDivElement>, handler?: (conversation: Conversation) => void) => {
            event.stopPropagation();
            setIsHovered(false);
            handler?.(conversation);
        },
        [conversation],
    );

    const onPinned = React.useCallback(async () => {
        await setPinned(conversation, !isPinned(conversation));
    }, [conversation, isPinned, setPinned]);

    const action = React.useMemo(
        () => (
            <div className={classes.action}>
                <Checkbox
                    className={classes.selectCheckbox}
                    checked={selectedForActions}
                    onChange={() => onSelectForActions?.(conversation, !selectedForActions)}
                />
                <Menu key={conversation.id} positioning="below-end">
                    <MenuTrigger disableButtonEnhancement>
                        <Button
                            appearance="transparent"
                            className={classes.moreButton}
                            icon={<MoreHorizontalRegular />}
                        />
                    </MenuTrigger>
                    <MenuPopover>
                        <MenuList>
                            <MenuItem
                                icon={isPinned(conversation) ? <PinOffRegular /> : <PinRegular />}
                                onClick={(event) => handleMenuItemClick(event, onPinned)}
                            >
                                {isPinned(conversation) ? 'Unpin' : 'Pin'}
                            </MenuItem>
                            <MenuItem
                                icon={hasUnreadMessages(conversation) ? <GlassesRegular /> : <GlassesOffRegular />}
                                onClick={(event) => {
                                    const hasUnread = hasUnreadMessages(conversation);
                                    handleMenuItemClick(event, hasUnread ? markAllAsRead : markAllAsUnread);
                                }}
                            >
                                {hasUnreadMessages(conversation) ? 'Mark read' : 'Mark unread'}
                            </MenuItem>
                            {onRename && (
                                <MenuItem
                                    icon={<EditRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onRename)}
                                    disabled={!owned}
                                >
                                    Rename
                                </MenuItem>
                            )}
                            <MenuItem
                                icon={<ArrowDownloadRegular />}
                                onClick={async (event) => handleMenuItemClick(event, onExport)}
                            >
                                Export
                            </MenuItem>
                            {onDuplicate && (
                                <MenuItem
                                    icon={<SaveCopyRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onDuplicate)}
                                >
                                    Duplicate
                                </MenuItem>
                            )}
                            {onShare && (
                                <MenuItem
                                    icon={<ShareRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onShare)}
                                >
                                    Share
                                </MenuItem>
                            )}
                            {onRemove && (
                                <MenuItem
                                    icon={<PlugDisconnectedRegular />}
                                    onClick={(event) => handleMenuItemClick(event, onRemove)}
                                    disabled={selected}
                                >
                                    {selected ? (
                                        <Tooltip
                                            content="Cannot remove currently active conversation"
                                            relationship="label"
                                        >
                                            <Text>Remove</Text>
                                        </Tooltip>
                                    ) : (
                                        'Remove'
                                    )}
                                </MenuItem>
                            )}
                        </MenuList>
                    </MenuPopover>
                </Menu>
            </div>
        ),
        [
            classes.action,
            classes.moreButton,
            classes.selectCheckbox,
            conversation,
            handleMenuItemClick,
            hasUnreadMessages,
            isPinned,
            markAllAsRead,
            markAllAsUnread,
            onDuplicate,
            onExport,
            onPinned,
            onRemove,
            onRename,
            onSelectForActions,
            onShare,
            owned,
            selected,
            selectedForActions,
        ],
    );

    const unread = hasUnreadMessages(conversation);

    const header = React.useMemo(() => {
        const formattedDate = Utility.toSimpleDateString(
            conversation.latest_message?.timestamp ?? conversation.created,
        );

        return (
            <div className={classes.header}>
                {isPinned(conversation) && (
                    <div className={classes.pin}>
                        <Pin12Regular />
                    </div>
                )}
                <Text className={classes.title} weight={unread ? 'bold' : 'regular'}>
                    {conversation.title}
                </Text>
                {!showActions && (
                    <Caption1 className={mergeClasses(classes.date, unread ? classes.unread : undefined)}>
                        {formattedDate}
                    </Caption1>
                )}
            </div>
        );
    }, [
        conversation,
        classes.header,
        classes.pin,
        classes.title,
        classes.date,
        classes.unread,
        showActions,
        isPinned,
        unread,
    ]);

    const description = React.useMemo(() => {
        if (!conversation.latest_message) {
            return undefined;
        }

        const participantId = conversation.latest_message.sender.participantId;
        const sender = conversation.participants.find((p) => p.id === participantId);
        const content = conversation.latest_message.content;

        return <Caption1 className={classes.description}>{sender ? `${sender.name}: ${content}` : content}</Caption1>;
    }, [conversation.latest_message, conversation.participants, classes.description]);

    const sortedParticipantsByOwnerMeOthers = React.useMemo(() => {
        const participants: ConversationParticipant[] = [];
        const owner = getOwnerParticipant(conversation);
        if (owner) {
            participants.push(owner);
        }
        if (wasSharedWithMe(conversation)) {
            const me = conversation.participants.find((participant) => participant.id === localUserId);
            if (me) {
                participants.push(me);
            }
        }
        const others = conversation.participants
            .filter((participant) => !participants.includes(participant))
            .filter((participant) => participant.active);
        participants.push(...others);
        return participants;
    }, [getOwnerParticipant, conversation, wasSharedWithMe, localUserId]);

    return (
        <Card
            size="small"
            appearance="subtle"
            selected={selected}
            onSelectionChange={() => onSelect?.(conversation)}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            floatingAction={showActions ? action : undefined}
        >
            <CardHeader
                className={mergeClasses(classes.cardHeader, showActions ? classes.showingActions : undefined)}
                image={<MemoizedParticipantAvatarGroup participants={sortedParticipantsByOwnerMeOthers} />}
                header={header}
                description={description}
            />
        </Card>
    );
};

export const MemoizedConversationItem = React.memo(ConversationItem, (prevProps, nextProps) =>
    Utility.deepEqual(prevProps, nextProps),
);
